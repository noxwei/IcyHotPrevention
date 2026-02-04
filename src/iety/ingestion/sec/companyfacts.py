"""SEC EDGAR companyfacts ingestion pipeline."""

import hashlib
from datetime import datetime, date
from typing import Any, Optional
import logging


def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse date string to date object.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        date object or None if invalid
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from iety.config import get_settings
from iety.cost.rate_limiter import rate_limited
from iety.ingestion.base import BasePipeline, PipelineCheckpoint

logger = logging.getLogger(__name__)


def compute_cik_hash(cik: str) -> int:
    """Compute hash for CIK partitioning.

    Args:
        cik: Company CIK number

    Returns:
        Integer hash for partition routing
    """
    return int(hashlib.md5(cik.encode()).hexdigest(), 16) % 8


class SECCompanyFactsPipeline(BasePipeline[dict, str]):
    """Pipeline for ingesting SEC EDGAR companyfacts.

    Fetches financial facts from SEC's public API for companies
    potentially involved in immigration enforcement contracts.

    Data source: data.sec.gov/api/xbrl/companyfacts/
    Rate limit: 10 requests per second
    """

    pipeline_name = "sec_companyfacts"
    default_batch_size = 10  # Small batches due to rate limit

    def __init__(
        self,
        session: AsyncSession,
        cik_list: Optional[list[str]] = None,
        batch_size: Optional[int] = None,
    ):
        """Initialize SEC pipeline.

        Args:
            session: Database session
            cik_list: List of CIKs to fetch (if None, uses default list)
            batch_size: Batch size for processing
        """
        super().__init__(session, batch_size)
        self.settings = get_settings().sec

        # Default CIKs for immigration enforcement contractors
        self.cik_list = cik_list or [
            "0000923796",  # GEO Group (private prisons)
            "0001070985",  # CoreCivic (private prisons)
            "0001321655",  # Palantir (ICE data systems)
            "0000040533",  # General Dynamics (IT services)
            "0001336920",  # Leidos (border technology)
            "0000072945",  # Northrop Grumman (surveillance)
            "0000202058",  # L3Harris (detection systems)
            "0000082267",  # Raytheon (border security tech)
        ]

        self.client = httpx.AsyncClient(
            base_url=self.settings.base_url,
            timeout=30.0,
            headers={
                "User-Agent": self.settings.user_agent,
                "Accept": "application/json",
            },
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    @rate_limited("sec")
    async def _fetch_companyfacts(self, cik: str) -> Optional[dict]:
        """Fetch companyfacts for a single CIK.

        Args:
            cik: CIK number (with leading zeros)

        Returns:
            Companyfacts data or None if not found
        """
        # Ensure CIK is properly padded
        cik_padded = cik.zfill(10)
        url = f"/api/xbrl/companyfacts/CIK{cik_padded}.json"

        try:
            response = await self.client.get(url)
            if response.status_code == 404:
                logger.warning(f"No companyfacts for CIK {cik}")
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"SEC API error for CIK {cik}: {e}")
            return None

    async def fetch_batch(
        self, checkpoint: PipelineCheckpoint
    ) -> tuple[list[dict], PipelineCheckpoint]:
        """Fetch a batch of companyfacts.

        Args:
            checkpoint: Current checkpoint with offset into CIK list

        Returns:
            Tuple of (records, new_checkpoint)
        """
        offset = checkpoint.offset
        batch_ciks = self.cik_list[offset : offset + self.batch_size]

        if not batch_ciks:
            return [], checkpoint

        records = []
        for cik in batch_ciks:
            data = await self._fetch_companyfacts(cik)
            if data:
                records.append(data)

        new_checkpoint = PipelineCheckpoint(
            offset=offset + len(batch_ciks),
            metadata={"total_ciks": len(self.cik_list)},
        )

        return records, new_checkpoint

    async def transform(self, record: dict) -> Optional[dict]:
        """Transform companyfacts response to database records.

        Note: This returns a list of fact records for a single company.
        The caller handles batching.

        Args:
            record: Raw companyfacts response

        Returns:
            Dict with company info and extracted facts
        """
        try:
            cik = str(record.get("cik", "")).zfill(10)
            entity_name = record.get("entityName", "")
            facts = record.get("facts", {})

            # Extract facts from US-GAAP taxonomy
            extracted_facts = []
            us_gaap = facts.get("us-gaap", {})

            # Focus on revenue and government contract related tags
            relevant_tags = [
                "Revenues",
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "ContractWithCustomerLiability",
                "ContractReceivableNet",
                "GovernmentContractsReceivable",
                "CostOfGoodsAndServicesSold",
                "NetIncomeLoss",
                "OperatingIncomeLoss",
            ]

            for tag, tag_data in us_gaap.items():
                if tag not in relevant_tags:
                    continue

                label = tag_data.get("label", tag)
                description = tag_data.get("description", "")
                units = tag_data.get("units", {})

                for unit, values in units.items():
                    for val in values:
                        extracted_facts.append({
                            "cik": cik,
                            "taxonomy": "us-gaap",
                            "tag": tag,
                            "label": label,
                            "description": description,
                            "unit": unit,
                            "value": val.get("val"),
                            "start_date": parse_date(val.get("start")),
                            "end_date": parse_date(val.get("end")),
                            "filed": parse_date(val.get("filed")),
                            "form": val.get("form"),
                            "accession_number": val.get("accn"),
                            "fiscal_year": val.get("fy"),
                            "fiscal_period": val.get("fp"),
                            "cik_hash": compute_cik_hash(cik),
                        })

            return {
                "cik": cik,
                "entity_name": entity_name,
                "facts": extracted_facts,
            }

        except Exception as e:
            logger.error(f"Transform error: {e}")
            return None

    async def upsert(self, records: list[dict]) -> int:
        """Upsert company facts to the database.

        Args:
            records: Transformed records with company info and facts

        Returns:
            Number of fact records affected
        """
        if not records:
            return 0

        # First upsert companies
        company_sql = text("""
            INSERT INTO sec.companies (cik, name, updated_at)
            VALUES (:cik, :name, NOW())
            ON CONFLICT (cik) DO UPDATE SET
                name = EXCLUDED.name,
                updated_at = NOW()
        """)

        # Then upsert facts
        fact_sql = text("""
            INSERT INTO sec.companyfacts (
                cik, taxonomy, tag, label, description, unit, value,
                start_date, end_date, filed, form, accession_number,
                fiscal_year, fiscal_period, cik_hash
            )
            VALUES (
                :cik, :taxonomy, :tag, :label, :description, :unit, :value,
                :start_date, :end_date, :filed, :form, :accession_number,
                :fiscal_year, :fiscal_period, :cik_hash
            )
            ON CONFLICT (cik, taxonomy, tag, end_date, form, accession_number, cik_hash)
            DO UPDATE SET
                value = EXCLUDED.value,
                label = EXCLUDED.label
        """)

        total_affected = 0

        for record in records:
            # Upsert company
            await self.session.execute(
                company_sql,
                {"cik": record["cik"], "name": record["entity_name"]},
            )

            # Upsert facts
            for fact in record.get("facts", []):
                try:
                    await self.session.execute(fact_sql, fact)
                    total_affected += 1
                except Exception as e:
                    logger.error(f"Fact upsert error: {e}")

        await self.session.commit()
        return total_affected


async def create_sec_pipeline(
    session: AsyncSession,
    cik_list: Optional[list[str]] = None,
) -> SECCompanyFactsPipeline:
    """Factory function to create SEC pipeline."""
    return SECCompanyFactsPipeline(session, cik_list)
