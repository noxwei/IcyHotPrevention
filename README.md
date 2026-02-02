# IETY - Immigration Enforcement Transparency Infrastructure

Multi-source data aggregation system for tracking immigration enforcement through federal spending, SEC disclosures, legal filings, and global news events.

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Start database
docker compose -f docker/docker-compose.yml up -d

# Run migrations
alembic upgrade head

# CLI
iety status
iety cost
iety ingest sec --max-batches=1
iety search "immigration enforcement"
```

## Budget Constraint

< $50/month total API costs
