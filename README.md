# IETY - Immigration Enforcement Transparency Infrastructure

Multi-source data aggregation system for tracking immigration enforcement through federal spending, SEC disclosures, legal filings, and global news events.

## Overview

IETY aggregates data from multiple public sources to provide transparency into immigration enforcement activities:

- **USASpending** - Federal contract awards to ICE/CBP (Treasury accounts 070-0540, 070-0543, 070-0532)
- **SEC EDGAR** - Financial disclosures from government contractors (GEO Group, CoreCivic, Palantir, etc.)
- **CourtListener** - Immigration-related legal filings and court opinions
- **GDELT** - Global news events related to immigration enforcement

## Features

- **Hybrid Search** - Vector similarity + keyword search with Reciprocal Rank Fusion (70/30 weighting)
- **Entity Resolution** - Cross-source entity linking using PostgreSQL trigram matching
- **Budget Protection** - Circuit breaker halts API calls at 95% of $50/month limit
- **Agent System** - Specialized personas (@Architect, @Ingestion, @Processor, @DBAdmin) with persistent memory
- **Checkpoint/Resume** - All pipelines support incremental sync with automatic recovery

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI (Typer + Rich)                       │
├─────────────────────────────────────────────────────────────────┤
│   Agents          │   Processing        │   Cost Control        │
│   ├── Architect   │   ├── Chunking      │   ├── Tracker         │
│   ├── Ingestion   │   ├── Embeddings    │   ├── Circuit Breaker │
│   ├── Processor   │   ├── Search        │   └── Rate Limiter    │
│   └── DBAdmin     │   └── Entity Res.   │                       │
├─────────────────────────────────────────────────────────────────┤
│                    Ingestion Pipelines                          │
│   USASpending  │  SEC EDGAR  │  CourtListener  │  GDELT         │
├─────────────────────────────────────────────────────────────────┤
│                PostgreSQL + pgvector                            │
│   usaspending │ sec │ legal │ gdelt │ integration               │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- (Optional) Voyage AI API key for embeddings

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/iety.git
cd iety

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### Database Setup

```bash
# Start PostgreSQL with pgvector
docker compose -f docker/docker-compose.yml up -d

# Run migrations
alembic upgrade head

# Verify setup
psql postgresql://iety:iety_dev_password@localhost:5432/iety \
  -c "SELECT * FROM integration.sync_state;"
```

### Running Pipelines

```bash
# Ingest SEC companyfacts (rate limited: 10 req/sec)
iety ingest sec --max-batches=5

# Ingest USASpending awards
iety ingest usaspending --max-batches=10

# Ingest CourtListener opinions
iety ingest legal --max-batches=5

# Poll GDELT for recent events
iety ingest gdelt --max-batches=1

# Dry run (no database writes)
iety ingest sec --max-batches=1 --dry-run
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `iety status` | System status (budget, sync state, database) |
| `iety cost` | Monthly cost breakdown by service |
| `iety ingest <source>` | Run ingestion pipeline |
| `iety search "<query>"` | Hybrid vector+keyword search |
| `iety agent <persona> "<task>"` | Execute task via agent |
| `iety memories <persona>` | View agent memories |
| `iety schema` | Output database DDL |
| `iety dashboard` | Interactive Rich dashboard |

### Search Examples

```bash
# Hybrid search (default)
iety search "immigration detention contracts"

# Vector-only search
iety search "deportation proceedings" --type vector

# Filter by schema
iety search "ICE facilities" --schema usaspending

# Limit results
iety search "asylum" --limit 5
```

## Configuration

All settings are configured via environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_*` | Database connection | localhost:5432 |
| `VOYAGE_API_KEY` | Voyage AI embeddings | (required for search) |
| `SEC_USER_AGENT` | SEC EDGAR User-Agent | (required) |
| `COURTLISTENER_API_KEY` | CourtListener API | (optional) |
| `BUDGET_MONTHLY_LIMIT` | Monthly budget cap | $50.00 |
| `BUDGET_HALT_THRESHOLD` | Auto-halt percentage | 95% |

## Budget & Cost Control

IETY is designed to operate under **$50/month**:

| Service | Rate | Estimated Monthly |
|---------|------|-------------------|
| Voyage AI (voyage-3.5-lite) | $0.02/1M tokens | ~$1-2 |
| All APIs | Free tiers | $0 |
| PostgreSQL | Self-hosted | $0 |
| **Total** | | **~$5/month** |

### Circuit Breaker

```
Budget Status:
├── 0-90%   → NORMAL (all operations allowed)
├── 90-95%  → WARNING (logged, operations continue)
└── 95%+    → HALTED (paid API calls blocked)
```

## Database Schema

Five schemas with partitioned tables:

| Schema | Tables | Partitioning |
|--------|--------|--------------|
| `usaspending` | awards, transactions, recipients | BY RANGE (fiscal_year) |
| `sec` | companies, companyfacts, filings | BY HASH (cik) - 8 partitions |
| `legal` | courts, dockets, opinions, parties | None |
| `gdelt` | events, mentions, gkg | BY RANGE (month_key) |
| `integration` | embeddings, entities, cost_log, agent_memory | HNSW index on vectors |

## Agent System

Four specialized agent personas with persistent memory:

| Agent | Responsibility | Tools |
|-------|----------------|-------|
| **@Architect** | Budget, privacy, architecture decisions | Cost tracking, approval |
| **@Ingestion** | Data pipelines, API integration | Rate limiters, checkpoints |
| **@Processor** | Embeddings, search, entity resolution | Voyage AI, pgvector |
| **@DBAdmin** | Schema design, query optimization | Migrations, indexes |

```bash
# Ask architect to review budget
iety agent architect "Review current budget status"

# Get ingestion advice
iety agent ingestion "Configure SEC pipeline"

# Check processor capabilities
iety agent processor "Estimate embedding cost for 10000 documents"
```

## Testing

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest --cov=iety tests/

# Run specific test file
pytest tests/unit/test_circuit_breaker.py -v
```

Current test coverage:
- Cost control (circuit breaker, rate limiter) - **24 tests**
- Processing (chunking) - **11 tests**

## Project Structure

```
iety/
├── docker/                    # Docker Compose + init scripts
├── migrations/versions/       # Alembic migrations (001-006)
├── src/iety/
│   ├── config.py             # Pydantic settings
│   ├── db/                   # Async SQLAlchemy engine
│   ├── ingestion/            # Pipeline implementations
│   │   ├── usaspending/
│   │   ├── sec/
│   │   ├── legal/
│   │   └── gdelt/
│   ├── processing/           # Chunking, embeddings, search
│   ├── cost/                 # Budget tracking & protection
│   ├── agents/               # Agent personas & memory
│   └── cli/                  # Typer CLI & Rich dashboard
├── tests/
│   ├── unit/
│   └── integration/
├── pyproject.toml
└── .env.example
```

## API Rate Limits

| Source | Limit | Implementation |
|--------|-------|----------------|
| SEC EDGAR | 10 req/sec | Token bucket |
| CourtListener | 5000 req/hour | Token bucket |
| Voyage AI | 100 req/sec | Token bucket |
| USASpending | 100 req/sec | Token bucket |
| GDELT | 10 req/sec | Token bucket |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`pytest tests/`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity search for PostgreSQL
- [Voyage AI](https://www.voyageai.com/) - Embedding models
- [CourtListener](https://www.courtlistener.com/) - Legal data API
- [USASpending](https://www.usaspending.gov/) - Federal spending data
- [GDELT](https://www.gdeltproject.org/) - Global events database
