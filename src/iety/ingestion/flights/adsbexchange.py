"""ADS-B Exchange flight tracking pipeline.

Alternative to OpenSky - community-run, more accessible for personal use.
Uses RapidAPI (free tier: 10,000 calls/month).
"""

from datetime import datetime, timezone
from typing import Optional
import logging

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from iety.ingestion.base import BasePipeline, PipelineCheckpoint

logger = logging.getLogger(__name__)


class ADSBExchangePipeline(BasePipeline[dict, str]):
    """Pipeline for tracking ICE charter aircraft via ADS-B Exchange.

    ADS-B Exchange is community-run and more accessible than OpenSky.
    Uses RapidAPI for access:
    - Free tier: 10,000 calls/month
    - Basic: $10/month for 100,000 calls

    Sign up: https://rapidapi.com/adsbx/api/adsbexchange-com1
    """

    pipeline_name = "adsbx_flights"
    default_batch_size = 10

    def __init__(
        self,
        session: AsyncSession,
        api_key: Optional[str] = None,
        batch_size: Optional[int] = None,
    ):
        super().__init__(session, batch_size)
        self.api_key = api_key

        headers = {
            "Accept": "application/json",
        }
        if api_key:
            headers["X-RapidAPI-Key"] = api_key
            headers["X-RapidAPI-Host"] = "adsbexchange-com1.p.rapidapi.com"

        self.client = httpx.AsyncClient(
            base_url="https://adsbexchange-com1.p.rapidapi.com/v2",
            timeout=30.0,
            headers=headers,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def _get_tracked_aircraft(self) -> list[dict]:
        """Get list of ICE charter aircraft from database."""
        sql = text("""
            SELECT icao24, registration, operator, aircraft_type
            FROM flights.aircraft
            WHERE is_ice_charter = TRUE
        """)
        result = await self.session.execute(sql)
        return [dict(row._mapping) for row in result]

    async def _fetch_by_icao24(self, icao24: str) -> Optional[dict]:
        """Fetch aircraft state by ICAO24 hex code.

        Args:
            icao24: Aircraft ICAO24 hex code

        Returns:
            Aircraft state dictionary or None
        """
        if not self.api_key:
            logger.warning("No ADS-B Exchange API key configured")
            return None

        try:
            response = await self.client.get(f"/icao/{icao24.upper()}/")
            response.raise_for_status()
            data = response.json()

            aircraft_list = data.get("ac", [])
            if not aircraft_list:
                return None

            ac = aircraft_list[0]
            return {
                "icao24": ac.get("hex", "").lower(),
                "callsign": (ac.get("flight") or "").strip(),
                "registration": ac.get("r"),
                "aircraft_type": ac.get("t"),
                "longitude": ac.get("lon"),
                "latitude": ac.get("lat"),
                "altitude_m": self._feet_to_meters(ac.get("alt_baro")),
                "on_ground": ac.get("alt_baro") == "ground",
                "velocity_ms": self._knots_to_ms(ac.get("gs")),
                "heading": ac.get("track"),
                "vertical_rate": self._fpm_to_ms(ac.get("baro_rate")),
                "squawk": ac.get("squawk"),
                "observed_at": datetime.now(timezone.utc),
            }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("ADS-B Exchange rate limit reached")
            else:
                logger.error(f"ADS-B Exchange API error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"ADS-B Exchange fetch error: {e}")
            return None

    async def _fetch_by_registration(self, registration: str) -> Optional[dict]:
        """Fetch aircraft state by registration (N-number).

        Args:
            registration: Aircraft registration (e.g., N802WA)

        Returns:
            Aircraft state dictionary or None
        """
        if not self.api_key:
            return None

        try:
            response = await self.client.get(f"/registration/{registration}/")
            response.raise_for_status()
            data = response.json()

            aircraft_list = data.get("ac", [])
            if not aircraft_list:
                return None

            ac = aircraft_list[0]
            return {
                "icao24": ac.get("hex", "").lower(),
                "callsign": (ac.get("flight") or "").strip(),
                "registration": ac.get("r"),
                "longitude": ac.get("lon"),
                "latitude": ac.get("lat"),
                "altitude_m": self._feet_to_meters(ac.get("alt_baro")),
                "on_ground": ac.get("alt_baro") == "ground",
                "velocity_ms": self._knots_to_ms(ac.get("gs")),
                "heading": ac.get("track"),
                "vertical_rate": self._fpm_to_ms(ac.get("baro_rate")),
                "observed_at": datetime.now(timezone.utc),
            }

        except Exception as e:
            logger.error(f"ADS-B Exchange fetch error for {registration}: {e}")
            return None

    @staticmethod
    def _feet_to_meters(feet) -> Optional[float]:
        """Convert feet to meters."""
        if feet is None or feet == "ground":
            return None
        try:
            return float(feet) * 0.3048
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _knots_to_ms(knots) -> Optional[float]:
        """Convert knots to meters per second."""
        if knots is None:
            return None
        try:
            return float(knots) * 0.514444
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _fpm_to_ms(fpm) -> Optional[float]:
        """Convert feet per minute to meters per second."""
        if fpm is None:
            return None
        try:
            return float(fpm) * 0.00508
        except (ValueError, TypeError):
            return None

    async def fetch_batch(
        self, checkpoint: PipelineCheckpoint
    ) -> tuple[list[dict], PipelineCheckpoint]:
        """Fetch current positions of tracked ICE aircraft."""
        aircraft = await self._get_tracked_aircraft()
        if not aircraft:
            logger.warning("No ICE charter aircraft configured for tracking")
            return [], checkpoint

        observations = []
        for ac in aircraft:
            # Try ICAO24 first, fall back to registration
            state = await self._fetch_by_icao24(ac["icao24"])
            if not state and ac.get("registration"):
                state = await self._fetch_by_registration(ac["registration"])

            if state:
                observations.append(state)

        new_checkpoint = PipelineCheckpoint(
            last_date=datetime.now(timezone.utc),
            metadata={
                "aircraft_tracked": len(aircraft),
                "observations": len(observations),
            },
        )

        return observations, new_checkpoint

    async def transform(self, record: dict) -> Optional[dict]:
        """Transform ADS-B Exchange state to database format."""
        return {
            "icao24": record["icao24"],
            "callsign": record.get("callsign"),
            "origin_country": "United States",  # All tracked aircraft are US-registered
            "longitude": record.get("longitude"),
            "latitude": record.get("latitude"),
            "altitude_m": record.get("altitude_m"),
            "velocity_ms": record.get("velocity_ms"),
            "heading": record.get("heading"),
            "vertical_rate": record.get("vertical_rate"),
            "on_ground": record.get("on_ground"),
            "observed_at": record.get("observed_at"),
        }

    async def upsert(self, records: list[dict]) -> int:
        """Insert flight observations."""
        if not records:
            return 0

        sql = text("""
            INSERT INTO flights.observations (
                icao24, callsign, origin_country, longitude, latitude,
                altitude_m, velocity_ms, heading, vertical_rate,
                on_ground, observed_at
            )
            VALUES (
                :icao24, :callsign, :origin_country, :longitude, :latitude,
                :altitude_m, :velocity_ms, :heading, :vertical_rate,
                :on_ground, :observed_at
            )
        """)

        affected = 0
        for record in records:
            try:
                await self.session.execute(sql, record)
                affected += 1
            except Exception as e:
                logger.error(f"Observation insert error: {e}")

        await self.session.commit()
        return affected

    async def poll_once(self) -> dict:
        """Poll current aircraft positions once."""
        aircraft = await self._get_tracked_aircraft()

        observations = []
        for ac in aircraft:
            state = await self._fetch_by_icao24(ac["icao24"])
            if state:
                observations.append(state)
                transformed = await self.transform(state)
                if transformed:
                    await self.upsert([transformed])

        return {
            "tracked": len(aircraft),
            "airborne": len([o for o in observations if not o.get("on_ground")]),
            "observations": observations,
        }


async def create_adsbx_pipeline(
    session: AsyncSession,
    api_key: Optional[str] = None,
) -> ADSBExchangePipeline:
    """Factory function to create ADS-B Exchange pipeline."""
    return ADSBExchangePipeline(session, api_key)
