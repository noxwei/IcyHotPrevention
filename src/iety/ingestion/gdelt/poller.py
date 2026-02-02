"""GDELT global events 15-minute poller pipeline."""

import csv
import io
import zipfile
from datetime import datetime, timezone
from typing import Optional
import logging

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from iety.config import get_settings
from iety.cost.rate_limiter import rate_limited
from iety.ingestion.base import BasePipeline, PipelineCheckpoint

logger = logging.getLogger(__name__)


# GDELT v2 Events column names
GDELT_EVENTS_COLUMNS = [
    "GLOBALEVENTID", "SQLDATE", "MonthYear", "Year", "FractionDate",
    "Actor1Code", "Actor1Name", "Actor1CountryCode", "Actor1KnownGroupCode",
    "Actor1EthnicCode", "Actor1Religion1Code", "Actor1Religion2Code",
    "Actor1Type1Code", "Actor1Type2Code", "Actor1Type3Code",
    "Actor2Code", "Actor2Name", "Actor2CountryCode", "Actor2KnownGroupCode",
    "Actor2EthnicCode", "Actor2Religion1Code", "Actor2Religion2Code",
    "Actor2Type1Code", "Actor2Type2Code", "Actor2Type3Code",
    "IsRootEvent", "EventCode", "EventBaseCode", "EventRootCode",
    "QuadClass", "GoldsteinScale", "NumMentions", "NumSources", "NumArticles",
    "AvgTone",
    "Actor1Geo_Type", "Actor1Geo_FullName", "Actor1Geo_CountryCode",
    "Actor1Geo_ADM1Code", "Actor1Geo_Lat", "Actor1Geo_Long",
    "Actor1Geo_FeatureID",
    "Actor2Geo_Type", "Actor2Geo_FullName", "Actor2Geo_CountryCode",
    "Actor2Geo_ADM1Code", "Actor2Geo_Lat", "Actor2Geo_Long",
    "Actor2Geo_FeatureID",
    "ActionGeo_Type", "ActionGeo_FullName", "ActionGeo_CountryCode",
    "ActionGeo_ADM1Code", "ActionGeo_Lat", "ActionGeo_Long",
    "ActionGeo_FeatureID",
    "DATEADDED", "SOURCEURL",
]

# Immigration-related CAMEO event codes
IMMIGRATION_EVENT_CODES = {
    "0311",  # Appeal for migration
    "0312",  # Appeal for return
    "0331",  # Appeal for humanitarian aid
    "0332",  # Appeal for asylum
    "0333",  # Appeal for protection
    "0431",  # Appeal to yield borders
    "0831",  # Make statement on refugees
    "0832",  # Make statement on migration
    "0833",  # Make statement on asylum
    "1011",  # Refuse asylum
    "1012",  # Refuse entry
    "1031",  # Deport
    "1311",  # Threaten to deport
    "1711",  # Detain for immigration
    "1721",  # Arrest for immigration
}


class GDELTPoller(BasePipeline[dict, str]):
    """Pipeline for polling GDELT 15-minute update files.

    Fetches the latest GDELT events CSV and filters for
    immigration-related events.

    Data source: data.gdeltproject.org
    Update frequency: Every 15 minutes
    """

    pipeline_name = "gdelt_events"
    default_batch_size = 1000

    def __init__(
        self,
        session: AsyncSession,
        batch_size: Optional[int] = None,
        filter_immigration: bool = True,
    ):
        """Initialize GDELT poller.

        Args:
            session: Database session
            batch_size: Batch size for processing
            filter_immigration: If True, only import immigration-related events
        """
        super().__init__(session, batch_size)
        self.settings = get_settings().gdelt
        self.filter_immigration = filter_immigration

        self.client = httpx.AsyncClient(
            timeout=120.0,  # Large files may take time
            follow_redirects=True,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    @rate_limited("gdelt")
    async def _get_latest_update_url(self) -> Optional[str]:
        """Get URL for the latest GDELT update file.

        Returns:
            URL to the latest events CSV or None
        """
        response = await self.client.get(self.settings.csv_url)
        response.raise_for_status()

        # Parse the lastupdate.txt file
        # Format: size hash url
        lines = response.text.strip().split("\n")
        for line in lines:
            parts = line.split()
            if len(parts) >= 3:
                url = parts[2]
                if "export.CSV" in url:
                    return url

        return None

    @rate_limited("gdelt")
    async def _download_and_parse_csv(self, url: str) -> list[dict]:
        """Download and parse GDELT CSV file.

        Args:
            url: URL to CSV (possibly zipped)

        Returns:
            List of event records
        """
        response = await self.client.get(url)
        response.raise_for_status()

        content = response.content

        # Handle zip files
        if url.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                # Get the first CSV file
                for name in zf.namelist():
                    if name.endswith(".CSV"):
                        content = zf.read(name)
                        break

        # Parse CSV
        text_content = content.decode("utf-8", errors="ignore")
        reader = csv.DictReader(
            io.StringIO(text_content),
            fieldnames=GDELT_EVENTS_COLUMNS,
            delimiter="\t",
        )

        records = []
        for row in reader:
            # Filter for immigration-related events if enabled
            if self.filter_immigration:
                event_code = row.get("EventCode", "")
                if event_code not in IMMIGRATION_EVENT_CODES:
                    # Also check for US-related events with migration keywords
                    actor1_country = row.get("Actor1CountryCode", "")
                    actor2_country = row.get("Actor2CountryCode", "")
                    action_country = row.get("ActionGeo_CountryCode", "")

                    # Keep events involving US immigration agencies
                    actor1_code = row.get("Actor1Code", "")
                    actor2_code = row.get("Actor2Code", "")

                    us_immigration = any([
                        "USA" in actor1_country and "GOV" in actor1_code,
                        "USA" in actor2_country and "GOV" in actor2_code,
                        actor1_code in ("USAGOV", "USAGOVICE", "USAGOVCBP"),
                        actor2_code in ("USAGOV", "USAGOVICE", "USAGOVCBP"),
                    ])

                    if not us_immigration:
                        continue

            records.append(row)

        return records

    async def fetch_batch(
        self, checkpoint: PipelineCheckpoint
    ) -> tuple[list[dict], PipelineCheckpoint]:
        """Fetch the latest GDELT update.

        Args:
            checkpoint: Current checkpoint

        Returns:
            Tuple of (records, new_checkpoint)
        """
        # Get the latest update URL
        url = await self._get_latest_update_url()
        if not url:
            logger.warning("Could not get GDELT update URL")
            return [], checkpoint

        # Check if we've already processed this URL
        last_url = checkpoint.metadata.get("last_url")
        if last_url == url:
            logger.debug(f"Already processed {url}")
            return [], checkpoint

        # Download and parse
        logger.info(f"Downloading GDELT update: {url}")
        records = await self._download_and_parse_csv(url)

        new_checkpoint = PipelineCheckpoint(
            last_date=datetime.now(timezone.utc),
            metadata={
                "last_url": url,
                "records_in_file": len(records),
            },
        )

        return records, new_checkpoint

    async def transform(self, record: dict) -> Optional[dict]:
        """Transform GDELT CSV row to database format.

        Args:
            record: Raw CSV row

        Returns:
            Transformed record or None to skip
        """
        try:
            sqldate_str = record.get("SQLDATE", "")
            if not sqldate_str:
                return None

            # Parse YYYYMMDD date
            sqldate = datetime.strptime(sqldate_str, "%Y%m%d").date()
            month_key = sqldate.strftime("%Y-%m")

            def safe_float(val):
                try:
                    return float(val) if val else None
                except (ValueError, TypeError):
                    return None

            def safe_int(val):
                try:
                    return int(val) if val else None
                except (ValueError, TypeError):
                    return None

            def safe_bool(val):
                return val == "1" if val else None

            return {
                "global_event_id": record.get("GLOBALEVENTID"),
                "sqldate": sqldate,
                "month_key": month_key,
                "year": safe_int(record.get("Year")),
                "month": int(sqldate_str[4:6]) if len(sqldate_str) >= 6 else None,
                "day": int(sqldate_str[6:8]) if len(sqldate_str) >= 8 else None,
                "fraction_date": safe_float(record.get("FractionDate")),
                "actor1_code": record.get("Actor1Code"),
                "actor1_name": record.get("Actor1Name"),
                "actor1_country_code": record.get("Actor1CountryCode"),
                "actor1_known_group_code": record.get("Actor1KnownGroupCode"),
                "actor1_ethnic_code": record.get("Actor1EthnicCode"),
                "actor1_religion1_code": record.get("Actor1Religion1Code"),
                "actor1_religion2_code": record.get("Actor1Religion2Code"),
                "actor1_type1_code": record.get("Actor1Type1Code"),
                "actor1_type2_code": record.get("Actor1Type2Code"),
                "actor1_type3_code": record.get("Actor1Type3Code"),
                "actor2_code": record.get("Actor2Code"),
                "actor2_name": record.get("Actor2Name"),
                "actor2_country_code": record.get("Actor2CountryCode"),
                "actor2_known_group_code": record.get("Actor2KnownGroupCode"),
                "actor2_ethnic_code": record.get("Actor2EthnicCode"),
                "actor2_religion1_code": record.get("Actor2Religion1Code"),
                "actor2_religion2_code": record.get("Actor2Religion2Code"),
                "actor2_type1_code": record.get("Actor2Type1Code"),
                "actor2_type2_code": record.get("Actor2Type2Code"),
                "actor2_type3_code": record.get("Actor2Type3Code"),
                "is_root_event": safe_bool(record.get("IsRootEvent")),
                "event_code": record.get("EventCode"),
                "event_base_code": record.get("EventBaseCode"),
                "event_root_code": record.get("EventRootCode"),
                "quad_class": safe_int(record.get("QuadClass")),
                "goldstein_scale": safe_float(record.get("GoldsteinScale")),
                "num_mentions": safe_int(record.get("NumMentions")),
                "num_sources": safe_int(record.get("NumSources")),
                "num_articles": safe_int(record.get("NumArticles")),
                "avg_tone": safe_float(record.get("AvgTone")),
                "actor1_geo_type": safe_int(record.get("Actor1Geo_Type")),
                "actor1_geo_fullname": record.get("Actor1Geo_FullName"),
                "actor1_geo_country_code": record.get("Actor1Geo_CountryCode"),
                "actor1_geo_adm1_code": record.get("Actor1Geo_ADM1Code"),
                "actor1_geo_lat": safe_float(record.get("Actor1Geo_Lat")),
                "actor1_geo_long": safe_float(record.get("Actor1Geo_Long")),
                "actor2_geo_type": safe_int(record.get("Actor2Geo_Type")),
                "actor2_geo_fullname": record.get("Actor2Geo_FullName"),
                "actor2_geo_country_code": record.get("Actor2Geo_CountryCode"),
                "actor2_geo_adm1_code": record.get("Actor2Geo_ADM1Code"),
                "actor2_geo_lat": safe_float(record.get("Actor2Geo_Lat")),
                "actor2_geo_long": safe_float(record.get("Actor2Geo_Long")),
                "action_geo_type": safe_int(record.get("ActionGeo_Type")),
                "action_geo_fullname": record.get("ActionGeo_FullName"),
                "action_geo_country_code": record.get("ActionGeo_CountryCode"),
                "action_geo_adm1_code": record.get("ActionGeo_ADM1Code"),
                "action_geo_lat": safe_float(record.get("ActionGeo_Lat")),
                "action_geo_long": safe_float(record.get("ActionGeo_Long")),
                "source_url": record.get("SOURCEURL"),
            }

        except Exception as e:
            logger.error(f"GDELT transform error: {e}")
            return None

    async def upsert(self, records: list[dict]) -> int:
        """Upsert GDELT events to the database.

        Args:
            records: Transformed records to upsert

        Returns:
            Number of records affected
        """
        if not records:
            return 0

        sql = text("""
            INSERT INTO gdelt.events (
                global_event_id, sqldate, month_key, year, month, day, fraction_date,
                actor1_code, actor1_name, actor1_country_code, actor1_known_group_code,
                actor1_ethnic_code, actor1_religion1_code, actor1_religion2_code,
                actor1_type1_code, actor1_type2_code, actor1_type3_code,
                actor2_code, actor2_name, actor2_country_code, actor2_known_group_code,
                actor2_ethnic_code, actor2_religion1_code, actor2_religion2_code,
                actor2_type1_code, actor2_type2_code, actor2_type3_code,
                is_root_event, event_code, event_base_code, event_root_code,
                quad_class, goldstein_scale, num_mentions, num_sources, num_articles,
                avg_tone,
                actor1_geo_type, actor1_geo_fullname, actor1_geo_country_code,
                actor1_geo_adm1_code, actor1_geo_lat, actor1_geo_long,
                actor2_geo_type, actor2_geo_fullname, actor2_geo_country_code,
                actor2_geo_adm1_code, actor2_geo_lat, actor2_geo_long,
                action_geo_type, action_geo_fullname, action_geo_country_code,
                action_geo_adm1_code, action_geo_lat, action_geo_long,
                source_url
            )
            VALUES (
                :global_event_id, :sqldate, :month_key, :year, :month, :day, :fraction_date,
                :actor1_code, :actor1_name, :actor1_country_code, :actor1_known_group_code,
                :actor1_ethnic_code, :actor1_religion1_code, :actor1_religion2_code,
                :actor1_type1_code, :actor1_type2_code, :actor1_type3_code,
                :actor2_code, :actor2_name, :actor2_country_code, :actor2_known_group_code,
                :actor2_ethnic_code, :actor2_religion1_code, :actor2_religion2_code,
                :actor2_type1_code, :actor2_type2_code, :actor2_type3_code,
                :is_root_event, :event_code, :event_base_code, :event_root_code,
                :quad_class, :goldstein_scale, :num_mentions, :num_sources, :num_articles,
                :avg_tone,
                :actor1_geo_type, :actor1_geo_fullname, :actor1_geo_country_code,
                :actor1_geo_adm1_code, :actor1_geo_lat, :actor1_geo_long,
                :actor2_geo_type, :actor2_geo_fullname, :actor2_geo_country_code,
                :actor2_geo_adm1_code, :actor2_geo_lat, :actor2_geo_long,
                :action_geo_type, :action_geo_fullname, :action_geo_country_code,
                :action_geo_adm1_code, :action_geo_lat, :action_geo_long,
                :source_url
            )
            ON CONFLICT (id, month_key) DO NOTHING
        """)

        affected = 0
        for record in records:
            try:
                await self.session.execute(sql, record)
                affected += 1
            except Exception as e:
                logger.error(f"GDELT upsert error: {e}")

        await self.session.commit()
        return affected


async def create_gdelt_pipeline(
    session: AsyncSession,
    filter_immigration: bool = True,
) -> GDELTPoller:
    """Factory function to create GDELT pipeline."""
    return GDELTPoller(session, filter_immigration=filter_immigration)
