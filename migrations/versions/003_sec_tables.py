"""SEC EDGAR schema tables.

Revision ID: 003
Revises: 002
Create Date: 2024-01-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create companies table
    op.execute("""
        CREATE TABLE sec.companies (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            cik TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            ticker TEXT,
            sic_code TEXT,
            sic_description TEXT,
            state_of_incorporation TEXT,
            fiscal_year_end TEXT,
            business_address JSONB,
            mailing_address JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Create companyfacts table - partitioned by CIK hash
    op.execute("""
        CREATE TABLE sec.companyfacts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            cik TEXT NOT NULL,
            taxonomy TEXT NOT NULL,
            tag TEXT NOT NULL,
            label TEXT,
            description TEXT,
            unit TEXT,
            value NUMERIC,
            start_date DATE,
            end_date DATE,
            filed DATE,
            form TEXT,
            accession_number TEXT,
            fiscal_year INTEGER,
            fiscal_period TEXT,
            cik_hash INTEGER NOT NULL,
            raw_data JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(cik, taxonomy, tag, end_date, form, accession_number)
        ) PARTITION BY HASH (cik_hash)
    """)

    # Create 8 hash partitions
    for i in range(8):
        op.execute(f"""
            CREATE TABLE sec.companyfacts_p{i}
            PARTITION OF sec.companyfacts
            FOR VALUES WITH (MODULUS 8, REMAINDER {i})
        """)

    # Create filings table
    op.execute("""
        CREATE TABLE sec.filings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            accession_number TEXT NOT NULL UNIQUE,
            cik TEXT NOT NULL,
            form_type TEXT NOT NULL,
            filed_date DATE,
            accepted_datetime TIMESTAMPTZ,
            document_count INTEGER,
            primary_document TEXT,
            primary_doc_description TEXT,
            items JSONB,
            raw_data JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Create exhibits table for 8-K and other relevant exhibits
    op.execute("""
        CREATE TABLE sec.exhibits (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            filing_id UUID REFERENCES sec.filings(id),
            accession_number TEXT NOT NULL,
            sequence INTEGER,
            document_type TEXT,
            filename TEXT,
            description TEXT,
            size_bytes INTEGER,
            content_text TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # Create indexes
    op.execute("CREATE INDEX idx_companies_name ON sec.companies USING gin (name gin_trgm_ops)")
    op.execute("CREATE INDEX idx_companies_ticker ON sec.companies (ticker)")
    op.execute("CREATE INDEX idx_companies_sic ON sec.companies (sic_code)")
    op.execute("CREATE INDEX idx_companyfacts_cik ON sec.companyfacts (cik)")
    op.execute("CREATE INDEX idx_companyfacts_tag ON sec.companyfacts (tag)")
    op.execute("CREATE INDEX idx_companyfacts_filed ON sec.companyfacts (filed)")
    op.execute("CREATE INDEX idx_filings_cik ON sec.filings (cik)")
    op.execute("CREATE INDEX idx_filings_form ON sec.filings (form_type)")
    op.execute("CREATE INDEX idx_filings_date ON sec.filings (filed_date)")
    op.execute("CREATE INDEX idx_exhibits_filing ON sec.exhibits (filing_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS sec.exhibits CASCADE")
    op.execute("DROP TABLE IF EXISTS sec.filings CASCADE")
    op.execute("DROP TABLE IF EXISTS sec.companyfacts CASCADE")
    op.execute("DROP TABLE IF EXISTS sec.companies CASCADE")
