"""USASpending data ingestion pipeline."""

from datetime import datetime
from typing import Any, Optional
import logging

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

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
            "sort": "Award ID",
            "order": "asc",
            "filters": filters or {},
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

        # Filter for ICE/CBP treasury accounts
        filters = {
            "tas_codes": [
                {"aid": "070", "main": "0540"},  # ICE Operations
                {"aid": "070", "main": "0543"},  # ICE Procurement
                {"aid": "070", "main": "0532"},  # CBP Operations
            ],
            "award_type_codes": [
                "A", "B", "C", "D",  # Contracts
                "IDV_A", "IDV_B", "IDV_C", "IDV_D", "IDV_E",  # IDVs
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
            start_date = record.get("Start Date")
            fiscal_year = None
            if start_date:
                dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                # Fiscal year: Oct-Dec = next year, Jan-Sep = current year
                fiscal_year = dt.year if dt.month >= 10 else dt.year

            return {
                "award_id": record.get("Award ID"),
                "award_type": record.get("Award Type"),
                "awarding_agency_name": record.get("Awarding Agency"),
                "awarding_agency_code": record.get("Awarding Agency Code"),
                "funding_agency_name": record.get("Funding Agency"),
                "funding_agency_code": record.get("Funding Agency Code"),
                "recipient_name": record.get("Recipient Name"),
                "recipient_uei": record.get("Recipient UEI"),
                "recipient_duns": record.get("Recipient DUNS"),
                "recipient_location": {
                    "city": record.get("Recipient City"),
                    "state": record.get("Recipient State"),
                    "country": record.get("Recipient Country"),
                    "zip": record.get("Recipient Zip Code"),
                },
                "total_obligation": record.get("Award Amount"),
                "award_description": record.get("Description"),
                "period_of_performance_start": start_date,
                "period_of_performance_end": record.get("End Date"),
                "fiscal_year": fiscal_year or datetime.now().year,
                "treasury_account_symbol": record.get("Treasury Account Symbol"),
                "naics_code": record.get("NAICS Code"),
                "naics_description": record.get("NAICS Description"),
                "psc_code": record.get("PSC Code"),
                "psc_description": record.get("PSC Description"),
                "place_of_performance": {
                    "city": record.get("Place of Performance City"),
                    "state": record.get("Place of Performance State"),
                    "country": record.get("Place of Performance Country"),
                    "zip": record.get("Place of Performance Zip Code"),
                },
                "raw_data": record,
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
                :recipient_uei, :recipient_duns, :recipient_location,
                :total_obligation, :award_description,
                :period_of_performance_start, :period_of_performance_end,
                :fiscal_year, :treasury_account_symbol, :naics_code, :naics_description,
                :psc_code, :psc_description, :place_of_performance, :raw_data,
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
