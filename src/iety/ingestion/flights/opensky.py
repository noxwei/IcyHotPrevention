"""OpenSky Network flight tracking pipeline.

Tracks known ICE charter aircraft using the free OpenSky API.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
import logging

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from iety.ingestion.base import BasePipeline, PipelineCheckpoint

logger = logging.getLogger(__name__)


class OpenSkyPipeline(BasePipeline[dict, str]):
    """Pipeline for tracking ICE charter aircraft via OpenSky Network.

    OpenSky provides free aircraft tracking data with:
    - Anonymous: 400 calls/day, 10-second resolution
    - Authenticated: 4,000+ calls/day, 5-second resolution

    Data source: opensky-network.org
    """

    pipeline_name = "opensky_flights"
    default_batch_size = 10  # Aircraft per batch

    def __init__(
        self,
        session: AsyncSession,
        username: Optional[str] = None,
        password: Optional[str] = None,
        batch_size: Optional[int] = None,
    ):
        super().__init__(session, batch_size)
        self.username = username
        self.password = password

        # Set up HTTP client with optional auth
        auth = None
        if username and password:
            auth = (username, password)

        self.client = httpx.AsyncClient(
            base_url="https://opensky-network.org/api",
            timeout=30.0,
            auth=auth,
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

    async def _fetch_aircraft_states(self, icao24_list: list[str]) -> list[dict]:
        """Fetch current state for multiple aircraft.

        Args:
            icao24_list: List of ICAO24 hex codes

        Returns:
            List of aircraft state dictionaries
        """
        if not icao24_list:
            return []

        # OpenSky allows filtering by icao24
        params = {"icao24": ",".join(icao24_list)}

        try:
            response = await self.client.get("/states/all", params=params)
            response.raise_for_status()
            data = response.json()

            states = data.get("states", [])
            if not states:
                return []

            # Parse state vectors
            # Format: [icao24, callsign, origin_country, time_position, last_contact,
            #          longitude, latitude, baro_altitude, on_ground, velocity,
            #          true_track, vertical_rate, sensors, geo_altitude, squawk,
            #          spi, position_source, category]
            parsed = []
            for state in states:
                if len(state) >= 17:
                    parsed.append({
                        "icao24": state[0],
                        "callsign": (state[1] or "").strip(),
                        "origin_country": state[2],
                        "longitude": state[5],
                        "latitude": state[6],
                        "altitude_m": state[7],  # barometric altitude
                        "on_ground": state[8],
                        "velocity_ms": state[9],
                        "heading": state[10],
                        "vertical_rate": state[11],
                        "observed_at": datetime.fromtimestamp(
                            state[4] or state[3], tz=timezone.utc
                        ),
                    })
            return parsed

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenSky API error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"OpenSky fetch error: {e}")
            return []

    async def _fetch_flight_history(
        self, icao24: str, begin: int, end: int
    ) -> list[dict]:
        """Fetch flight history for an aircraft.

        Args:
            icao24: Aircraft ICAO24 code
            begin: Start timestamp (Unix)
            end: End timestamp (Unix)

        Returns:
            List of flight records
        """
        try:
            response = await self.client.get(
                "/flights/aircraft",
                params={"icao24": icao24, "begin": begin, "end": end},
            )
            response.raise_for_status()
            return response.json() or []
        except Exception as e:
            logger.error(f"Flight history error for {icao24}: {e}")
            return []

    async def fetch_batch(
        self, checkpoint: PipelineCheckpoint
    ) -> tuple[list[dict], PipelineCheckpoint]:
        """Fetch current positions of tracked ICE aircraft.

        Args:
            checkpoint: Current checkpoint

        Returns:
            Tuple of (observations, new_checkpoint)
        """
        # Get tracked aircraft
        aircraft = await self._get_tracked_aircraft()
        if not aircraft:
            logger.warning("No ICE charter aircraft configured for tracking")
            return [], checkpoint

        icao24_list = [a["icao24"] for a in aircraft]

        # Fetch current states
        observations = await self._fetch_aircraft_states(icao24_list)

        new_checkpoint = PipelineCheckpoint(
            last_date=datetime.now(timezone.utc),
            metadata={
                "aircraft_tracked": len(icao24_list),
                "observations": len(observations),
            },
        )

        return observations, new_checkpoint

    async def transform(self, record: dict) -> Optional[dict]:
        """Transform OpenSky state to database format.

        Args:
            record: Raw OpenSky state

        Returns:
            Transformed record
        """
        return {
            "icao24": record["icao24"],
            "callsign": record.get("callsign"),
            "origin_country": record.get("origin_country"),
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
        """Insert flight observations.

        Args:
            records: Transformed observation records

        Returns:
            Number of records inserted
        """
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
        """Poll current aircraft positions once.

        Returns:
            Dict with aircraft positions
        """
        aircraft = await self._get_tracked_aircraft()
        icao24_list = [a["icao24"] for a in aircraft]

        observations = await self._fetch_aircraft_states(icao24_list)

        # Insert observations
        for obs in observations:
            transformed = await self.transform(obs)
            if transformed:
                await self.upsert([transformed])

        return {
            "tracked": len(icao24_list),
            "airborne": len([o for o in observations if not o.get("on_ground")]),
            "observations": observations,
        }


async def create_opensky_pipeline(
    session: AsyncSession,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> OpenSkyPipeline:
    """Factory function to create OpenSky pipeline."""
    return OpenSkyPipeline(session, username, password)
