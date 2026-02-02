"""Pytest configuration and fixtures for IETY tests."""

import os
from unittest.mock import AsyncMock, MagicMock
import pytest


# Set test environment
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "true")


@pytest.fixture
def mock_session():
    """Create a mock async database session."""
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(fetchone=MagicMock(return_value=None)))
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_cost_tracker(mock_session):
    """Create a mock cost tracker."""
    from iety.cost.tracker import CostTracker

    tracker = CostTracker(mock_session)
    return tracker


@pytest.fixture
def mock_embedding_service():
    """Create a mock embedding service."""
    service = MagicMock()
    service.embed_texts = AsyncMock(return_value=[
        MagicMock(embedding=[0.1] * 1024, token_count=100, content_hash="abc123")
    ])
    service.embed_query = AsyncMock(return_value=[0.1] * 1024)
    return service


@pytest.fixture
def mock_memory_store(mock_session):
    """Create a mock memory store."""
    from iety.agents.memory.store import MemoryStore

    store = MemoryStore(mock_session)
    return store


@pytest.fixture
def sample_usaspending_record():
    """Sample USASpending API response record."""
    return {
        "Award ID": "TEST-001",
        "Award Type": "Contract",
        "Awarding Agency": "Department of Homeland Security",
        "Awarding Agency Code": "070",
        "Funding Agency": "Immigration and Customs Enforcement",
        "Funding Agency Code": "070",
        "Recipient Name": "Test Contractor Inc",
        "Recipient UEI": "ABC123DEF456",
        "Recipient DUNS": "123456789",
        "Recipient City": "Washington",
        "Recipient State": "DC",
        "Recipient Country": "USA",
        "Award Amount": 1000000.00,
        "Description": "Immigration enforcement services",
        "Start Date": "2024-01-01",
        "End Date": "2024-12-31",
        "Treasury Account Symbol": "070-0540",
        "NAICS Code": "561210",
        "NAICS Description": "Facilities Support Services",
    }


@pytest.fixture
def sample_sec_companyfacts():
    """Sample SEC companyfacts API response."""
    return {
        "cik": "0001234567",
        "entityName": "Test Company Inc",
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "label": "Revenues",
                    "description": "Total revenues",
                    "units": {
                        "USD": [
                            {
                                "val": 1000000000,
                                "start": "2023-01-01",
                                "end": "2023-12-31",
                                "filed": "2024-02-15",
                                "form": "10-K",
                                "accn": "0001234567-24-000001",
                                "fy": 2023,
                                "fp": "FY",
                            }
                        ]
                    },
                }
            }
        },
    }


@pytest.fixture
def sample_gdelt_event():
    """Sample GDELT event record."""
    return {
        "GLOBALEVENTID": "123456789",
        "SQLDATE": "20240115",
        "Year": "2024",
        "Actor1Code": "USAGOV",
        "Actor1Name": "UNITED STATES",
        "Actor1CountryCode": "USA",
        "Actor2Code": "MEX",
        "Actor2Name": "MEXICO",
        "Actor2CountryCode": "MEX",
        "IsRootEvent": "1",
        "EventCode": "1012",  # Refuse entry
        "EventBaseCode": "101",
        "EventRootCode": "10",
        "GoldsteinScale": "-2.0",
        "NumMentions": "10",
        "NumSources": "5",
        "NumArticles": "3",
        "AvgTone": "-1.5",
        "ActionGeo_CountryCode": "US",
        "SOURCEURL": "https://example.com/article",
    }
