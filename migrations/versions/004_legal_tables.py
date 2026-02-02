"""Legal filings schema tables (CourtListener).

Revision ID: 004
Revises: 003
Create Date: 2024-01-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create courts table
    op.execute("""
        CREATE TABLE legal.courts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            court_id TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            short_name TEXT,
            citation_string TEXT,
            jurisdiction TEXT,
            url TEXT,
            start_date DATE,
            end_date DATE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Create dockets table
    op.execute("""
        CREATE TABLE legal.dockets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            docket_id TEXT NOT NULL UNIQUE,
            court_id TEXT REFERENCES legal.courts(court_id),
            case_name TEXT,
            docket_number TEXT,
            date_filed DATE,
            date_terminated DATE,
            date_last_filing DATE,
            cause TEXT,
            nature_of_suit TEXT,
            jury_demand TEXT,
            jurisdiction_type TEXT,
            appellate_fee_status TEXT,
            appellate_case_type_info JSONB,
            parties JSONB,
            attorneys JSONB,
            pacer_case_id TEXT,
            assigned_to TEXT,
            referred_to TEXT,
            raw_data JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Create opinions table
    op.execute("""
        CREATE TABLE legal.opinions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            opinion_id TEXT NOT NULL UNIQUE,
            docket_id TEXT REFERENCES legal.dockets(docket_id),
            cluster_id TEXT,
            court_id TEXT,
            case_name TEXT,
            date_filed DATE,
            author TEXT,
            author_str TEXT,
            per_curiam BOOLEAN DEFAULT FALSE,
            type TEXT,
            sha1 TEXT,
            download_url TEXT,
            local_path TEXT,
            plain_text TEXT,
            html TEXT,
            citations JSONB,
            precedential_status TEXT,
            raw_data JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Create docket_entries table
    op.execute("""
        CREATE TABLE legal.docket_entries (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            entry_id TEXT NOT NULL UNIQUE,
            docket_id TEXT REFERENCES legal.dockets(docket_id),
            entry_number INTEGER,
            date_filed DATE,
            date_entered DATE,
            description TEXT,
            pacer_doc_id TEXT,
            pacer_seq_no TEXT,
            documents JSONB,
            raw_data JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Create parties table
    op.execute("""
        CREATE TABLE legal.parties (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            party_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            party_type TEXT,
            extra_info TEXT,
            date_terminated DATE,
            attorneys JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Create indexes
    op.execute("CREATE INDEX idx_dockets_case_name ON legal.dockets USING gin (case_name gin_trgm_ops)")
    op.execute("CREATE INDEX idx_dockets_court ON legal.dockets (court_id)")
    op.execute("CREATE INDEX idx_dockets_date_filed ON legal.dockets (date_filed)")
    op.execute("CREATE INDEX idx_dockets_nature_of_suit ON legal.dockets (nature_of_suit)")
    op.execute("CREATE INDEX idx_opinions_docket ON legal.opinions (docket_id)")
    op.execute("CREATE INDEX idx_opinions_date ON legal.opinions (date_filed)")
    op.execute("CREATE INDEX idx_opinions_case_name ON legal.opinions USING gin (case_name gin_trgm_ops)")
    op.execute("CREATE INDEX idx_docket_entries_docket ON legal.docket_entries (docket_id)")
    op.execute("CREATE INDEX idx_docket_entries_date ON legal.docket_entries (date_filed)")
    op.execute("CREATE INDEX idx_parties_name ON legal.parties USING gin (name gin_trgm_ops)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS legal.parties CASCADE")
    op.execute("DROP TABLE IF EXISTS legal.docket_entries CASCADE")
    op.execute("DROP TABLE IF EXISTS legal.opinions CASCADE")
    op.execute("DROP TABLE IF EXISTS legal.dockets CASCADE")
    op.execute("DROP TABLE IF EXISTS legal.courts CASCADE")
