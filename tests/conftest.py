"""
Pytest configuration and fixtures for MusicBrainz MCP testing.

This module provides common fixtures, test configuration, and mock data
for testing all components of the MusicBrainz MCP server.
"""

import asyncio
import json
import pytest
import sys
import os
from typing import Dict, Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from musicbrainz_mcp.musicbrainz_client import MusicBrainzClient
from musicbrainz_mcp.config import MusicBrainzMCPConfig, APIConfig, CacheConfig
from musicbrainz_mcp.utils import CacheUtils
from musicbrainz_mcp.server import create_server
from fastmcp import Client


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "api: mark test as requiring API access"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_api_config():
    """Provide a test API configuration."""
    return APIConfig(
        base_url="https://test.musicbrainz.org/ws/2",
        user_agent="TestMusicBrainzMCP/1.0.0",
        rate_limit=10.0,  # Higher rate limit for testing
        timeout=5.0,      # Shorter timeout for testing
        max_retries=1,
        retry_delay=0.1
    )


@pytest.fixture
def mock_cache_config():
    """Provide a test cache configuration."""
    return CacheConfig(
        enabled=True,
        default_ttl=60,   # Shorter TTL for testing
        max_entries=100,  # Smaller cache for testing
        cleanup_interval=10,
        search_ttl=30,
        lookup_ttl=60,
        browse_ttl=45
    )


@pytest.fixture
def test_config(mock_api_config, mock_cache_config):
    """Provide a complete test configuration."""
    config = MusicBrainzMCPConfig()
    config.api = mock_api_config
    config.cache = mock_cache_config
    config.debug = True
    config.environment = "testing"
    return config


@pytest.fixture
def cache_utils():
    """Provide a fresh CacheUtils instance for testing."""
    return CacheUtils(default_ttl=60)


@pytest.fixture
async def mock_musicbrainz_client(mock_api_config):
    """Provide a mocked MusicBrainz client."""
    client = MusicBrainzClient(
        user_agent=mock_api_config.user_agent,
        rate_limit=mock_api_config.rate_limit,
        timeout=mock_api_config.timeout
    )
    
    # Mock the HTTP client
    client._session = AsyncMock()
    
    return client


@pytest.fixture
async def real_musicbrainz_client(mock_api_config):
    """Provide a real MusicBrainz client for integration tests."""
    client = MusicBrainzClient(
        user_agent=mock_api_config.user_agent,
        rate_limit=1.0,  # Respect real API rate limits
        timeout=mock_api_config.timeout
    )
    
    async with client:
        yield client


@pytest.fixture
async def mcp_server():
    """Provide an MCP server instance for testing."""
    server = create_server()
    return server


@pytest.fixture
async def mcp_client(mcp_server):
    """Provide an MCP client connected to the test server."""
    async with Client(mcp_server) as client:
        yield client


# Mock data fixtures
@pytest.fixture
def mock_artist_data():
    """Provide mock artist data for testing."""
    return {
        "id": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
        "name": "The Beatles",
        "sort-name": "Beatles, The",
        "disambiguation": "",
        "type": "Group",
        "type-id": "e431f5f6-b5d2-343d-8b36-72607fffb74b",
        "gender": None,
        "country": "GB",
        "life-span": {
            "begin": "1960",
            "end": "1970",
            "ended": True
        },
        "area": {
            "id": "8a754a16-0027-3a29-b6d7-2b40ea0481ed",
            "name": "United Kingdom",
            "sort-name": "United Kingdom",
            "iso-3166-1-codes": ["GB"]
        }
    }


@pytest.fixture
def mock_release_data():
    """Provide mock release data for testing."""
    return {
        "id": "f4a261d1-2a31-4d1a-b4b6-7d6e4c8f9a0b",
        "title": "Abbey Road",
        "disambiguation": "",
        "date": "1969-09-26",
        "country": "GB",
        "status": "Official",
        "status-id": "4e304316-386d-3409-af2e-78857eec5cfe",
        "packaging": "None",
        "text-representation": {
            "language": "eng",
            "script": "Latn"
        },
        "artist-credit": [
            {
                "name": "The Beatles",
                "artist": {
                    "id": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
                    "name": "The Beatles",
                    "sort-name": "Beatles, The"
                }
            }
        ]
    }


@pytest.fixture
def mock_recording_data():
    """Provide mock recording data for testing."""
    return {
        "id": "c1a2b3d4-e5f6-7890-abcd-ef1234567890",
        "title": "Come Together",
        "disambiguation": "",
        "length": 259000,  # 4:19 in milliseconds
        "video": False,
        "artist-credit": [
            {
                "name": "The Beatles",
                "artist": {
                    "id": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
                    "name": "The Beatles",
                    "sort-name": "Beatles, The"
                }
            }
        ],
        "isrcs": ["GBUM71505078"]
    }


@pytest.fixture
def mock_search_response():
    """Provide mock search response data."""
    return {
        "created": "2023-01-01T00:00:00.000Z",
        "count": 1,
        "offset": 0,
        "artists": [
            {
                "id": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
                "name": "The Beatles",
                "sort-name": "Beatles, The",
                "type": "Group",
                "country": "GB",
                "score": 100
            }
        ]
    }


@pytest.fixture
def mock_browse_response():
    """Provide mock browse response data."""
    return {
        "release-count": 2,
        "release-offset": 0,
        "releases": [
            {
                "id": "f4a261d1-2a31-4d1a-b4b6-7d6e4c8f9a0b",
                "title": "Abbey Road",
                "date": "1969-09-26",
                "status": "Official"
            },
            {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "title": "Let It Be",
                "date": "1970-05-08",
                "status": "Official"
            }
        ]
    }


@pytest.fixture
def mock_http_response():
    """Provide a mock HTTP response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {"test": "data"}
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def mock_httpx_client():
    """Provide a mock httpx client."""
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {"test": "data"}
    mock_response.raise_for_status.return_value = None
    mock_client.get.return_value = mock_response
    return mock_client


# Utility fixtures
@pytest.fixture
def valid_mbid():
    """Provide a valid MBID for testing."""
    return "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"


@pytest.fixture
def invalid_mbid():
    """Provide an invalid MBID for testing."""
    return "invalid-mbid-format"


@pytest.fixture
def sample_search_query():
    """Provide a sample search query."""
    return "The Beatles"


@pytest.fixture
def sample_pagination_params():
    """Provide sample pagination parameters."""
    return {"limit": 25, "offset": 0}


# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_global_state():
    """Clean up global state between tests."""
    # Clear any global cache
    from musicbrainz_mcp.utils import get_cache
    cache = get_cache()
    cache.clear()
    
    # Reset global config
    from musicbrainz_mcp.config import set_config, MusicBrainzMCPConfig
    set_config(MusicBrainzMCPConfig())
    
    yield
    
    # Cleanup after test
    cache.clear()
    set_config(MusicBrainzMCPConfig())
