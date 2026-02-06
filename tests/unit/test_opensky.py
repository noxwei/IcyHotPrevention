"""Unit tests for OpenSky null timestamp handling."""

from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

import httpx
import pytest

from iety.ingestion.flights.opensky import OpenSkyPipeline


def _make_state_vector(
    icao24="abc123",
    callsign="TEST01  ",
    origin_country="United States",
    time_position=None,
    last_contact=None,
    longitude=-77.0,
    latitude=38.9,
    baro_altitude=10000.0,
    on_ground=False,
    velocity=250.0,
    true_track=180.0,
    vertical_rate=0.0,
    sensors=None,
    geo_altitude=10000.0,
    squawk=None,
    spi=False,
    position_source=0,
    category=0,
):
    """Build a state vector list matching OpenSky format."""
    return [
        icao24, callsign, origin_country, time_position, last_contact,
        longitude, latitude, baro_altitude, on_ground, velocity,
        true_track, vertical_rate, sensors, geo_altitude, squawk,
        spi, position_source, category,
    ]


@pytest.fixture
def pipeline():
    """Create an OpenSkyPipeline with a mock session."""
    mock_session = AsyncMock()
    p = OpenSkyPipeline(session=mock_session)
    return p


class TestOpenSkyNullTimestamp:
    """Tests for null timestamp handling in _fetch_aircraft_states."""

    @pytest.mark.asyncio
    async def test_both_timestamps_none_skips_observation(self, pipeline):
        """When both time_position and last_contact are None, skip the observation."""
        state = _make_state_vector(
            icao24="abc123",
            time_position=None,
            last_contact=None,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"states": [state]}
        mock_response.raise_for_status = MagicMock()

        pipeline.client = AsyncMock()
        pipeline.client.get = AsyncMock(return_value=mock_response)

        result = await pipeline._fetch_aircraft_states(["abc123"])

        assert len(result) == 0  # Skipped, no crash

    @pytest.mark.asyncio
    async def test_only_last_contact_set_uses_fallback(self, pipeline):
        """When time_position is None but last_contact is set, use last_contact."""
        ts = 1700000000
        state = _make_state_vector(
            icao24="def456",
            time_position=None,
            last_contact=ts,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"states": [state]}
        mock_response.raise_for_status = MagicMock()

        pipeline.client = AsyncMock()
        pipeline.client.get = AsyncMock(return_value=mock_response)

        result = await pipeline._fetch_aircraft_states(["def456"])

        assert len(result) == 1
        expected_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        assert result[0]["observed_at"] == expected_dt

    @pytest.mark.asyncio
    async def test_both_timestamps_set_prefers_time_position(self, pipeline):
        """When both timestamps are set, prefer time_position (state[4])."""
        ts_position = 1700000100  # state[4] - time_position
        ts_contact = 1700000000   # state[3] - last_contact
        state = _make_state_vector(
            icao24="ghi789",
            time_position=ts_contact,   # state[3]
            last_contact=ts_position,   # state[4]
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"states": [state]}
        mock_response.raise_for_status = MagicMock()

        pipeline.client = AsyncMock()
        pipeline.client.get = AsyncMock(return_value=mock_response)

        result = await pipeline._fetch_aircraft_states(["ghi789"])

        assert len(result) == 1
        # state[4] or state[3] → state[4] is preferred when truthy
        expected_dt = datetime.fromtimestamp(ts_position, tz=timezone.utc)
        assert result[0]["observed_at"] == expected_dt
