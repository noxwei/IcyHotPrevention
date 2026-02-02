"""Create database schemas and extensions.

Revision ID: 001
Revises: None
Create Date: 2024-01-01
"""

from typing import Sequence, Union

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create extensions (if not already created by init.sql)
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"pg_trgm\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"vector\"")

    # Create schemas
    op.execute("CREATE SCHEMA IF NOT EXISTS usaspending")
    op.execute("CREATE SCHEMA IF NOT EXISTS sec")
    op.execute("CREATE SCHEMA IF NOT EXISTS legal")
    op.execute("CREATE SCHEMA IF NOT EXISTS gdelt")
    op.execute("CREATE SCHEMA IF NOT EXISTS integration")


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS integration CASCADE")
    op.execute("DROP SCHEMA IF EXISTS gdelt CASCADE")
    op.execute("DROP SCHEMA IF EXISTS legal CASCADE")
    op.execute("DROP SCHEMA IF EXISTS sec CASCADE")
    op.execute("DROP SCHEMA IF EXISTS usaspending CASCADE")
