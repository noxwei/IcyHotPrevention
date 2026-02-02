"""CourtListener legal filings ingestion pipeline."""

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


class CourtListenerPipeline(BasePipeline[dict, str]):
    """Pipeline for ingesting legal filings from CourtListener.

    Focuses on immigration-related cases using keyword search
    and specific court filters (immigration courts, federal courts).

    Data source: courtlistener.com API
    Rate limit: 5000 requests per hour
    """

    pipeline_name = "courtlistener"
    default_batch_size = 20  # API returns up to 20 results per page

    # Immigration-related search queries
    SEARCH_QUERIES = [
        "immigration detention",
        "ICE detention",
        "deportation",
        "removal proceedings",
        "immigration enforcement",
        "CBP",
        "border patrol",
        "asylum",
    ]

    def __init__(
        self,
        session: AsyncSession,
        search_query: Optional[str] = None,
        batch_size: Optional[int] = None,
    ):
        """Initialize CourtListener pipeline.

        Args:
            session: Database session
            search_query: Specific search query (uses defaults if None)
            batch_size: Batch size for processing
        """
        super().__init__(session, batch_size)
        self.settings = get_settings().courtlistener
        self.search_query = search_query or "immigration detention"

        headers = {
            "Accept": "application/json",
        }
        if self.settings.api_key:
            headers["Authorization"] = f"Token {self.settings.api_key.get_secret_value()}"

        self.client = httpx.AsyncClient(
            base_url=self.settings.base_url,
            timeout=60.0,
            headers=headers,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    @rate_limited("courtlistener")
    async def _search_opinions(self, cursor: Optional[str] = None) -> dict:
        """Search opinions via CourtListener API.

        Args:
            cursor: Pagination cursor

        Returns:
            API response with results and pagination
        """
        params = {
            "q": self.search_query,
            "order_by": "dateFiled desc",
            "type": "o",  # Opinions
        }

        if cursor:
            params["cursor"] = cursor

        response = await self.client.get("/search/", params=params)
        response.raise_for_status()
        return response.json()

    @rate_limited("courtlistener")
    async def _get_opinion_detail(self, opinion_id: str) -> Optional[dict]:
        """Fetch detailed opinion data.

        Args:
            opinion_id: Opinion ID

        Returns:
            Opinion details or None
        """
        try:
            response = await self.client.get(f"/opinions/{opinion_id}/")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError:
            return None

    @rate_limited("courtlistener")
    async def _get_docket(self, docket_id: str) -> Optional[dict]:
        """Fetch docket data.

        Args:
            docket_id: Docket ID

        Returns:
            Docket details or None
        """
        try:
            response = await self.client.get(f"/dockets/{docket_id}/")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError:
            return None

    async def fetch_batch(
        self, checkpoint: PipelineCheckpoint
    ) -> tuple[list[dict], PipelineCheckpoint]:
        """Fetch a batch of opinions from CourtListener.

        Args:
            checkpoint: Current checkpoint with cursor

        Returns:
            Tuple of (records, new_checkpoint)
        """
        try:
            data = await self._search_opinions(cursor=checkpoint.cursor)
        except httpx.HTTPStatusError as e:
            logger.error(f"CourtListener API error: {e}")
            raise

        results = data.get("results", [])
        next_cursor = data.get("next")

        # Extract cursor from next URL if present
        new_cursor = None
        if next_cursor:
            # Parse cursor from URL
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(next_cursor)
            params = parse_qs(parsed.query)
            new_cursor = params.get("cursor", [None])[0]

        new_checkpoint = PipelineCheckpoint(
            cursor=new_cursor,
            page=checkpoint.page + 1,
            metadata={
                "count": data.get("count", 0),
                "has_next": next_cursor is not None,
            },
        )

        if not results:
            return [], new_checkpoint

        return results, new_checkpoint

    async def transform(self, record: dict) -> Optional[dict]:
        """Transform CourtListener search result to database format.

        Args:
            record: Raw search result

        Returns:
            Transformed record or None to skip
        """
        try:
            # Extract opinion ID from resource_uri
            opinion_id = str(record.get("id", ""))

            # Parse dates
            date_filed = record.get("dateFiled")
            if date_filed:
                date_filed = datetime.fromisoformat(
                    date_filed.replace("Z", "+00:00")
                ).date()

            return {
                "opinion_id": opinion_id,
                "case_name": record.get("caseName"),
                "court_id": record.get("court"),
                "date_filed": date_filed,
                "docket_id": record.get("docket_id"),
                "citation": record.get("citation"),
                "snippet": record.get("snippet"),  # Search snippet
                "precedential_status": record.get("status"),
                "download_url": record.get("download_url"),
                "raw_data": record,
            }

        except Exception as e:
            logger.error(f"Transform error: {e}")
            return None

    async def upsert(self, records: list[dict]) -> int:
        """Upsert opinions to the database.

        Args:
            records: Transformed records to upsert

        Returns:
            Number of records affected
        """
        if not records:
            return 0

        sql = text("""
            INSERT INTO legal.opinions (
                opinion_id, case_name, court_id, date_filed,
                docket_id, precedential_status, download_url, raw_data
            )
            VALUES (
                :opinion_id, :case_name, :court_id, :date_filed,
                :docket_id, :precedential_status, :download_url, :raw_data
            )
            ON CONFLICT (opinion_id) DO UPDATE SET
                case_name = EXCLUDED.case_name,
                raw_data = EXCLUDED.raw_data
        """)

        affected = 0
        for record in records:
            try:
                # Remove non-DB fields
                db_record = {k: v for k, v in record.items() if k not in ("citation", "snippet")}
                await self.session.execute(sql, db_record)
                affected += 1
            except Exception as e:
                logger.error(f"Upsert error for opinion {record.get('opinion_id')}: {e}")

        await self.session.commit()
        return affected


class CourtListenerDocketPipeline(BasePipeline[dict, str]):
    """Pipeline for ingesting dockets from CourtListener.

    Fetches detailed docket information for immigration-related cases.
    """

    pipeline_name = "courtlistener_dockets"
    default_batch_size = 10

    def __init__(
        self,
        session: AsyncSession,
        nature_of_suit: Optional[str] = None,
        batch_size: Optional[int] = None,
    ):
        super().__init__(session, batch_size)
        self.settings = get_settings().courtlistener
        # Nature of Suit codes for immigration cases
        self.nature_of_suit = nature_of_suit or "462"  # Deportation

        headers = {"Accept": "application/json"}
        if self.settings.api_key:
            headers["Authorization"] = f"Token {self.settings.api_key.get_secret_value()}"

        self.client = httpx.AsyncClient(
            base_url=self.settings.base_url,
            timeout=60.0,
            headers=headers,
        )

    async def close(self) -> None:
        await self.client.aclose()

    @rate_limited("courtlistener")
    async def _search_dockets(self, cursor: Optional[str] = None) -> dict:
        """Search dockets by nature of suit."""
        params = {
            "nature_of_suit": self.nature_of_suit,
            "order_by": "-date_filed",
        }
        if cursor:
            params["cursor"] = cursor

        response = await self.client.get("/dockets/", params=params)
        response.raise_for_status()
        return response.json()

    async def fetch_batch(
        self, checkpoint: PipelineCheckpoint
    ) -> tuple[list[dict], PipelineCheckpoint]:
        data = await self._search_dockets(cursor=checkpoint.cursor)
        results = data.get("results", [])

        next_url = data.get("next")
        new_cursor = None
        if next_url:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(next_url)
            params = parse_qs(parsed.query)
            new_cursor = params.get("cursor", [None])[0]

        new_checkpoint = PipelineCheckpoint(
            cursor=new_cursor,
            page=checkpoint.page + 1,
        )

        return results, new_checkpoint

    async def transform(self, record: dict) -> Optional[dict]:
        try:
            return {
                "docket_id": str(record.get("id", "")),
                "court_id": record.get("court"),
                "case_name": record.get("case_name"),
                "docket_number": record.get("docket_number"),
                "date_filed": record.get("date_filed"),
                "date_terminated": record.get("date_terminated"),
                "nature_of_suit": record.get("nature_of_suit"),
                "cause": record.get("cause"),
                "jurisdiction_type": record.get("jurisdiction_type"),
                "pacer_case_id": record.get("pacer_case_id"),
                "assigned_to": record.get("assigned_to_str"),
                "referred_to": record.get("referred_to_str"),
                "raw_data": record,
            }
        except Exception as e:
            logger.error(f"Docket transform error: {e}")
            return None

    async def upsert(self, records: list[dict]) -> int:
        if not records:
            return 0

        sql = text("""
            INSERT INTO legal.dockets (
                docket_id, court_id, case_name, docket_number,
                date_filed, date_terminated, nature_of_suit, cause,
                jurisdiction_type, pacer_case_id, assigned_to, referred_to,
                raw_data, updated_at
            )
            VALUES (
                :docket_id, :court_id, :case_name, :docket_number,
                :date_filed, :date_terminated, :nature_of_suit, :cause,
                :jurisdiction_type, :pacer_case_id, :assigned_to, :referred_to,
                :raw_data, NOW()
            )
            ON CONFLICT (docket_id) DO UPDATE SET
                case_name = EXCLUDED.case_name,
                date_terminated = EXCLUDED.date_terminated,
                raw_data = EXCLUDED.raw_data,
                updated_at = NOW()
        """)

        affected = 0
        for record in records:
            try:
                await self.session.execute(sql, record)
                affected += 1
            except Exception as e:
                logger.error(f"Docket upsert error: {e}")

        await self.session.commit()
        return affected


async def create_courtlistener_pipeline(
    session: AsyncSession,
    search_query: Optional[str] = None,
) -> CourtListenerPipeline:
    """Factory function to create CourtListener pipeline."""
    return CourtListenerPipeline(session, search_query)
