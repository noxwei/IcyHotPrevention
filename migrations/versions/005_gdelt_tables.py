"""GDELT global events schema tables.

Revision ID: 005
Revises: 004
Create Date: 2024-01-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create events table - partitioned by month
    op.execute("""
        CREATE TABLE gdelt.events (
            id UUID DEFAULT gen_random_uuid(),
            global_event_id TEXT NOT NULL,
            sqldate DATE NOT NULL,
            month_key TEXT NOT NULL,
            year INTEGER,
            month INTEGER,
            day INTEGER,
            fraction_date NUMERIC(10, 4),
            actor1_code TEXT,
            actor1_name TEXT,
            actor1_country_code TEXT,
            actor1_known_group_code TEXT,
            actor1_ethnic_code TEXT,
            actor1_religion1_code TEXT,
            actor1_religion2_code TEXT,
            actor1_type1_code TEXT,
            actor1_type2_code TEXT,
            actor1_type3_code TEXT,
            actor2_code TEXT,
            actor2_name TEXT,
            actor2_country_code TEXT,
            actor2_known_group_code TEXT,
            actor2_ethnic_code TEXT,
            actor2_religion1_code TEXT,
            actor2_religion2_code TEXT,
            actor2_type1_code TEXT,
            actor2_type2_code TEXT,
            actor2_type3_code TEXT,
            is_root_event BOOLEAN,
            event_code TEXT,
            event_base_code TEXT,
            event_root_code TEXT,
            quad_class INTEGER,
            goldstein_scale NUMERIC(5, 2),
            num_mentions INTEGER,
            num_sources INTEGER,
            num_articles INTEGER,
            avg_tone NUMERIC(8, 4),
            actor1_geo_type INTEGER,
            actor1_geo_fullname TEXT,
            actor1_geo_country_code TEXT,
            actor1_geo_adm1_code TEXT,
            actor1_geo_lat NUMERIC(10, 6),
            actor1_geo_long NUMERIC(10, 6),
            actor2_geo_type INTEGER,
            actor2_geo_fullname TEXT,
            actor2_geo_country_code TEXT,
            actor2_geo_adm1_code TEXT,
            actor2_geo_lat NUMERIC(10, 6),
            actor2_geo_long NUMERIC(10, 6),
            action_geo_type INTEGER,
            action_geo_fullname TEXT,
            action_geo_country_code TEXT,
            action_geo_adm1_code TEXT,
            action_geo_lat NUMERIC(10, 6),
            action_geo_long NUMERIC(10, 6),
            date_added TIMESTAMPTZ,
            source_url TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            PRIMARY KEY (id, month_key)
        ) PARTITION BY RANGE (month_key)
    """)

    # Create partitions for recent months (2024-01 through 2026-12)
    months = []
    for year in range(2024, 2027):
        for month in range(1, 13):
            months.append(f"{year}-{month:02d}")

    for i, month_key in enumerate(months):
        if i + 1 < len(months):
            next_key = months[i + 1]
        else:
            next_key = "2027-01"
        op.execute(f"""
            CREATE TABLE gdelt.events_{month_key.replace('-', '_')}
            PARTITION OF gdelt.events
            FOR VALUES FROM ('{month_key}') TO ('{next_key}')
        """)

    # Create mentions table
    op.execute("""
        CREATE TABLE gdelt.mentions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            global_event_id TEXT NOT NULL,
            event_time_date TIMESTAMPTZ,
            mention_time_date TIMESTAMPTZ,
            mention_type INTEGER,
            mention_source_name TEXT,
            mention_identifier TEXT,
            sentence_id INTEGER,
            actor1_char_offset INTEGER,
            actor2_char_offset INTEGER,
            action_char_offset INTEGER,
            in_raw_text BOOLEAN,
            confidence INTEGER,
            mention_doc_len INTEGER,
            mention_doc_tone NUMERIC(8, 4),
            mention_doc_translation_info TEXT,
            extras TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Create gkg (Global Knowledge Graph) table
    op.execute("""
        CREATE TABLE gdelt.gkg (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            gkg_record_id TEXT NOT NULL UNIQUE,
            date TIMESTAMPTZ,
            source_collection_identifier INTEGER,
            source_common_name TEXT,
            document_identifier TEXT,
            counts JSONB,
            v2_counts JSONB,
            themes JSONB,
            v2_themes JSONB,
            locations JSONB,
            v2_locations JSONB,
            persons JSONB,
            v2_persons JSONB,
            organizations JSONB,
            v2_organizations JSONB,
            v2_tone JSONB,
            dates JSONB,
            gcam JSONB,
            sharing_image TEXT,
            related_images JSONB,
            social_image_embeds JSONB,
            social_video_embeds JSONB,
            quotations JSONB,
            all_names JSONB,
            amounts JSONB,
            translation_info JSONB,
            extras JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Create indexes
    op.execute("CREATE INDEX idx_events_date ON gdelt.events (sqldate)")
    op.execute("CREATE INDEX idx_events_actor1_country ON gdelt.events (actor1_country_code)")
    op.execute("CREATE INDEX idx_events_actor2_country ON gdelt.events (actor2_country_code)")
    op.execute("CREATE INDEX idx_events_event_code ON gdelt.events (event_code)")
    op.execute("CREATE INDEX idx_events_goldstein ON gdelt.events (goldstein_scale)")
    op.execute("CREATE INDEX idx_events_action_geo ON gdelt.events (action_geo_country_code)")
    op.execute("CREATE INDEX idx_mentions_event ON gdelt.mentions (global_event_id)")
    op.execute("CREATE INDEX idx_mentions_source ON gdelt.mentions (mention_source_name)")
    op.execute("CREATE INDEX idx_gkg_date ON gdelt.gkg (date)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS gdelt.gkg CASCADE")
    op.execute("DROP TABLE IF EXISTS gdelt.mentions CASCADE")
    op.execute("DROP TABLE IF EXISTS gdelt.events CASCADE")
