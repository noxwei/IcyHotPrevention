"""USASpending data ingestion pipeline."""

from datetime import datetime, date
from typing import Any, Optional
import json
import logging

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse date string to date object."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        return None

from iety.config import get_settings
from iety.cost.rate_limiter import rate_limited
from iety.ingestion.base import BasePipeline, PipelineCheckpoint

logger = logging.getLogger(__name__)


class USASpendingPipeline(BasePipeline[dict, str]):
    """Pipeline for ingesting USASpending federal contract data.

    Focuses on ICE/CBP funding using Treasury Account Symbols:
    - 070-0540: ICE Operations
    - 070-0543: ICE Procurement
    - 070-0532: CBP Operations

    Data source: api.usaspending.gov
    """

    pipeline_name = "usaspending"
    default_batch_size = 100

    def __init__(self, session: AsyncSession, batch_size: Optional[int] = None):
        super().__init__(session, batch_size)
        self.settings = get_settings().usaspending
        self.client = httpx.AsyncClient(
            base_url=self.settings.base_url,
            timeout=60.0,
            headers={"Content-Type": "application/json"},
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    @rate_limited("usaspending")
    async def _search_awards(
        self, page: int = 1, filters: Optional[dict] = None
    ) -> dict:
        """Search awards via USASpending API.

        Args:
            page: Page number (1-indexed)
            filters: Additional search filters

        Returns:
            API response with results and metadata
        """
        payload = {
            "page": page,
            "limit": self.batch_size,
            "sort": "Award Amount",
            "order": "desc",
            "filters": filters or {},
            "fields": [
                "Award ID", "Recipient Name", "Award Amount", "Description",
                "Start Date", "End Date", "Awarding Agency", "Awarding Sub Agency",
                "Recipient UEI", "NAICS Code", "NAICS Description",
                "PSC Code", "PSC Description"
            ],
        }

        response = await self.client.post("/search/spending_by_award/", json=payload)
        response.raise_for_status()
        return response.json()

    async def fetch_batch(
        self, checkpoint: PipelineCheckpoint
    ) -> tuple[list[dict], PipelineCheckpoint]:
        """Fetch a batch of awards from USASpending API.

        Args:
            checkpoint: Current checkpoint with page number

        Returns:
            Tuple of (records, new_checkpoint)
        """
        page = checkpoint.page + 1

        # Filter for ICE and CBP contracts (2018+ to match partitions)
        filters = {
            "agencies": [
                {"type": "awarding", "tier": "subtier", "name": "U.S. Immigration and Customs Enforcement"},
                {"type": "awarding", "tier": "subtier", "name": "U.S. Customs and Border Protection"},
            ],
            "time_period": [
                {"start_date": "2018-01-01", "end_date": "2027-12-31"}
            ],
            "award_type_codes": [
                "A", "B", "C", "D",  # Contracts
            ],
        }

        try:
            data = await self._search_awards(page=page, filters=filters)
        except httpx.HTTPStatusError as e:
            logger.error(f"USASpending API error: {e.response.status_code}")
            raise

        results = data.get("results", [])
        has_more = data.get("page_metadata", {}).get("hasNext", False)

        # Update checkpoint
        new_checkpoint = PipelineCheckpoint(
            page=page,
            metadata={
                "total": data.get("page_metadata", {}).get("total", 0),
                "has_next": has_more,
            },
        )

        # If no more results, return empty list to signal completion
        if not results or not has_more:
            if results:
                return results, new_checkpoint
            return [], new_checkpoint

        return results, new_checkpoint

    async def transform(self, record: dict) -> Optional[dict]:
        """Transform USASpending API record to database format.

        Args:
            record: Raw API record

        Returns:
            Transformed record or None to skip
        """
        try:
            # Extract fiscal year from dates
            start_date_str = record.get("Start Date")
            start_date = parse_date(start_date_str)
            end_date = parse_date(record.get("End Date"))

            fiscal_year = datetime.now().year
            if start_date:
                # Fiscal year: Oct-Dec = next year, Jan-Sep = current year
                fiscal_year = start_date.year + 1 if start_date.month >= 10 else start_date.year

            # Skip records outside partition range (2018-2026)
            if fiscal_year < 2018 or fiscal_year > 2026:
                logger.debug(f"Skipping {record.get('Award ID')} - FY {fiscal_year} outside partition range")
                return None

            return {
                "award_id": record.get("Award ID"),
                "award_type": record.get("Award Type"),
                "awarding_agency_name": record.get("Awarding Agency"),
                "awarding_agency_code": record.get("Awarding Sub Agency"),
                "funding_agency_name": record.get("Awarding Agency"),
                "funding_agency_code": None,
                "recipient_name": record.get("Recipient Name"),
                "recipient_uei": record.get("Recipient UEI"),
                "recipient_duns": None,
                "recipient_location": "{}",
                "total_obligation": record.get("Award Amount"),
                "award_description": record.get("Description"),
                "period_of_performance_start": start_date,
                "period_of_performance_end": end_date,
                "fiscal_year": fiscal_year,
                "treasury_account_symbol": None,
                "naics_code": record.get("NAICS Code"),
                "naics_description": record.get("NAICS Description"),
                "psc_code": record.get("PSC Code"),
                "psc_description": record.get("PSC Description"),
                "place_of_performance": "{}",
                "raw_data": json.dumps(record),
            }
        except Exception as e:
            logger.error(f"Transform error for {record.get('Award ID')}: {e}")
            return None

    async def upsert(self, records: list[dict]) -> int:
        """Upsert awards to the database.

        Args:
            records: Transformed records to upsert

        Returns:
            Number of records affected
        """
        if not records:
            return 0

        sql = text("""
            INSERT INTO usaspending.awards (
                award_id, award_type, awarding_agency_name, awarding_agency_code,
                funding_agency_name, funding_agency_code, recipient_name,
                recipient_uei, recipient_duns, recipient_location,
                total_obligation, award_description,
                period_of_performance_start, period_of_performance_end,
                fiscal_year, treasury_account_symbol, naics_code, naics_description,
                psc_code, psc_description, place_of_performance, raw_data,
                updated_at
            )
            VALUES (
                :award_id, :award_type, :awarding_agency_name, :awarding_agency_code,
                :funding_agency_name, :funding_agency_code, :recipient_name,
                :recipient_uei, :recipient_duns, CAST(:recipient_location AS JSONB),
                :total_obligation, :award_description,
                :period_of_performance_start, :period_of_performance_end,
                :fiscal_year, :treasury_account_symbol, :naics_code, :naics_description,
                :psc_code, :psc_description, CAST(:place_of_performance AS JSONB), CAST(:raw_data AS JSONB),
                NOW()
            )
            ON CONFLICT (award_id, fiscal_year) DO UPDATE SET
                award_type = EXCLUDED.award_type,
                awarding_agency_name = EXCLUDED.awarding_agency_name,
                funding_agency_name = EXCLUDED.funding_agency_name,
                recipient_name = EXCLUDED.recipient_name,
                recipient_uei = EXCLUDED.recipient_uei,
                total_obligation = EXCLUDED.total_obligation,
                award_description = EXCLUDED.award_description,
                raw_data = EXCLUDED.raw_data,
                updated_at = NOW()
        """)

        affected = 0
        for record in records:
            try:
                await self.session.execute(sql, record)
                affected += 1
            except Exception as e:
                logger.error(f"Upsert error for {record.get('award_id')}: {e}")

        await self.session.commit()
        return affected


async def create_usaspending_pipeline(session: AsyncSession) -> USASpendingPipeline:
    """Factory function to create USASpending pipeline."""
    return USASpendingPipeline(session)
