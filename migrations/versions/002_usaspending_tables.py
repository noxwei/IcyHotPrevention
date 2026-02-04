"""USASpending schema tables.

Revision ID: 002
Revises: 001
Create Date: 2024-01-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create awards table - partitioned by fiscal year
    op.execute("""
        CREATE TABLE usaspending.awards (
            id UUID DEFAULT gen_random_uuid(),
            award_id TEXT NOT NULL,
            award_type TEXT,
            awarding_agency_name TEXT,
            awarding_agency_code TEXT,
            funding_agency_name TEXT,
            funding_agency_code TEXT,
            recipient_name TEXT,
            recipient_uei TEXT,
            recipient_duns TEXT,
            recipient_location JSONB,
            total_obligation NUMERIC(20, 2),
            total_outlay NUMERIC(20, 2),
            award_description TEXT,
            period_of_performance_start DATE,
            period_of_performance_end DATE,
            fiscal_year INTEGER NOT NULL,
            treasury_account_symbol TEXT,
            naics_code TEXT,
            naics_description TEXT,
            psc_code TEXT,
            psc_description TEXT,
            place_of_performance JSONB,
            raw_data JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            PRIMARY KEY (id, fiscal_year),
            UNIQUE(award_id, fiscal_year)
        ) PARTITION BY RANGE (fiscal_year)
    """)

    # Create partitions for recent fiscal years
    for year in range(2018, 2027):
        op.execute(f"""
            CREATE TABLE usaspending.awards_{year}
            PARTITION OF usaspending.awards
            FOR VALUES FROM ({year}) TO ({year + 1})
        """)

    # Create transactions table
    op.execute("""
        CREATE TABLE usaspending.transactions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            transaction_id TEXT NOT NULL UNIQUE,
            award_id TEXT NOT NULL,
            transaction_type TEXT,
            action_date DATE,
            action_type TEXT,
            federal_action_obligation NUMERIC(20, 2),
            modification_number TEXT,
            description TEXT,
            raw_data JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Create recipients table for entity tracking
    op.execute("""
        CREATE TABLE usaspending.recipients (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            uei TEXT UNIQUE,
            duns TEXT,
            name TEXT NOT NULL,
            legal_business_name TEXT,
            parent_name TEXT,
            parent_uei TEXT,
            business_types JSONB,
            location JSONB,
            congressional_district TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Create indexes
    op.execute("CREATE INDEX idx_awards_recipient_name ON usaspending.awards USING gin (recipient_name gin_trgm_ops)")
    op.execute("CREATE INDEX idx_awards_agency_code ON usaspending.awards (funding_agency_code)")
    op.execute("CREATE INDEX idx_awards_treasury_account ON usaspending.awards (treasury_account_symbol)")
    op.execute("CREATE INDEX idx_awards_naics ON usaspending.awards (naics_code)")
    op.execute("CREATE INDEX idx_transactions_award ON usaspending.transactions (award_id)")
    op.execute("CREATE INDEX idx_transactions_date ON usaspending.transactions (action_date)")
    op.execute("CREATE INDEX idx_recipients_name ON usaspending.recipients USING gin (name gin_trgm_ops)")
    op.execute("CREATE INDEX idx_recipients_uei ON usaspending.recipients (uei)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS usaspending.transactions CASCADE")
    op.execute("DROP TABLE IF EXISTS usaspending.recipients CASCADE")
    op.execute("DROP TABLE IF EXISTS usaspending.awards CASCADE")
