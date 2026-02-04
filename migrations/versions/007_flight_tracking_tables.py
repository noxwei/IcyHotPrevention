"""Flight tracking tables for ICE Air monitoring.

Revision ID: 007
Revises: 006
Create Date: 2025-02-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create flights schema
    op.execute("CREATE SCHEMA IF NOT EXISTS flights")

    # Aircraft registry - known ICE charter aircraft
    op.execute("""
        CREATE TABLE flights.aircraft (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            icao24 TEXT NOT NULL UNIQUE,
            registration TEXT,
            operator TEXT,
            aircraft_type TEXT,
            is_ice_charter BOOLEAN DEFAULT FALSE,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Flight observations from OpenSky
    op.execute("""
        CREATE TABLE flights.observations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            icao24 TEXT NOT NULL,
            callsign TEXT,
            origin_country TEXT,
            longitude NUMERIC(12, 6),
            latitude NUMERIC(12, 6),
            altitude_m NUMERIC(10, 2),
            velocity_ms NUMERIC(10, 2),
            heading NUMERIC(6, 2),
            vertical_rate NUMERIC(10, 2),
            on_ground BOOLEAN,
            observed_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Flight tracks - aggregated flight paths
    op.execute("""
        CREATE TABLE flights.tracks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            icao24 TEXT NOT NULL,
            callsign TEXT,
            flight_date DATE NOT NULL,
            departure_airport TEXT,
            arrival_airport TEXT,
            departure_time TIMESTAMPTZ,
            arrival_time TIMESTAMPTZ,
            path JSONB,
            is_potential_ice_flight BOOLEAN DEFAULT FALSE,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Create indexes
    op.execute("CREATE INDEX idx_aircraft_icao24 ON flights.aircraft (icao24)")
    op.execute("CREATE INDEX idx_aircraft_registration ON flights.aircraft (registration)")
    op.execute("CREATE INDEX idx_aircraft_ice_charter ON flights.aircraft (is_ice_charter) WHERE is_ice_charter = TRUE")
    op.execute("CREATE INDEX idx_observations_icao24 ON flights.observations (icao24)")
    op.execute("CREATE INDEX idx_observations_time ON flights.observations (observed_at)")
    op.execute("CREATE INDEX idx_tracks_icao24_date ON flights.tracks (icao24, flight_date)")
    op.execute("CREATE INDEX idx_tracks_ice_flight ON flights.tracks (is_potential_ice_flight) WHERE is_potential_ice_flight = TRUE")

    # Insert known ICE charter aircraft (ICAO24 codes)
    # These are publicly documented ICE Air Operations aircraft
    op.execute("""
        INSERT INTO flights.aircraft (icao24, registration, operator, aircraft_type, is_ice_charter, notes) VALUES
        -- World Atlantic Airlines (ICE charter contractor)
        ('a15e46', 'N802WA', 'World Atlantic Airlines', 'MD-83', TRUE, 'ICE charter - documented'),
        ('a18b70', 'N803WA', 'World Atlantic Airlines', 'MD-83', TRUE, 'ICE charter - documented'),
        -- iAero Airways (formerly Swift Air)
        ('a64a7c', 'N406SW', 'iAero Airways', 'B737', TRUE, 'ICE charter - documented'),
        ('a64f8e', 'N407SW', 'iAero Airways', 'B737', TRUE, 'ICE charter - documented'),
        ('a654a0', 'N408SW', 'iAero Airways', 'B737', TRUE, 'ICE charter - documented'),
        -- CSI Aviation (ground transport but also some air)
        ('a5f806', 'N391CS', 'CSI Aviation', 'BE20', TRUE, 'ICE contractor'),
        -- Classic Air Charter
        ('a47ef9', 'N368CA', 'Classic Air Charter', 'B737', TRUE, 'ICE charter - documented')
        ON CONFLICT (icao24) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS flights.tracks CASCADE")
    op.execute("DROP TABLE IF EXISTS flights.observations CASCADE")
    op.execute("DROP TABLE IF EXISTS flights.aircraft CASCADE")
    op.execute("DROP SCHEMA IF EXISTS flights CASCADE")
