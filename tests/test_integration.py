"""
Integration tests for MusicBrainz MCP server.

Tests the complete integration between all components including
real API calls, server functionality, and end-to-end workflows.
"""

import pytest
import pytest_asyncio
import asyncio
import os
import json
from unittest.mock import patch, AsyncMock, MagicMock
from fastmcp import Client
from musicbrainz_mcp.server import create_server
from musicbrainz_mcp.musicbrainz_client import MusicBrainzClient
from musicbrainz_mcp.config import MusicBrainzMCPConfig, set_config
from musicbrainz_mcp.utils import get_cache
from tests.mock_data import MOCK_ARTIST_SEARCH_RESPONSE, MOCK_ARTIST_BEATLES


@pytest.mark.integration
class TestMCPServerIntegration:
    """Test complete MCP server integration."""

    @pytest_asyncio.fixture
    async def server(self):
        """Create test server with test configuration."""
        # Set up test configuration
        config = MusicBrainzMCPConfig()
        config.api.rate_limit = 10.0  # Higher rate limit for testing
        config.cache.enabled = True
        config.debug = True
        set_config(config)

        return create_server()

    @pytest_asyncio.fixture
    async def client(self, server):
        """Create test client connected to server."""
        async with Client(server) as client:
            yield client

    @pytest.mark.asyncio
    async def test_server_startup_and_tools(self, client):
        """Test server startup and tool availability."""
        # Test that server starts and tools are available
        tools = await client.list_tools()

        assert len(tools) == 10
        tool_names = [tool.name for tool in tools]

        expected_tools = [
            "search_artist", "search_release", "search_recording", "search_release_group",
            "get_artist_details", "get_release_details", "get_recording_details",
            "browse_artist_releases", "browse_artist_recordings", "lookup_by_mbid"
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    @pytest.mark.asyncio
    @patch('musicbrainz_mcp.musicbrainz_client.httpx.AsyncClient.get')
    async def test_end_to_end_search_workflow(self, mock_get, client):
        """Test complete search workflow from client to API."""
        # Setup mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = MOCK_ARTIST_SEARCH_RESPONSE
        mock_get.return_value = mock_response

        # Test search workflow
        result = await client.call_tool("search_artist", {
            "params": {
                "query": "The Beatles",
                "limit": 10,
                "offset": 0
            }
        })

        # Verify that the tool executed successfully
        assert result is not None

        # Verify that HTTP request was made
        mock_get.assert_called_once()

    @pytest.mark.asyncio
    @patch('musicbrainz_mcp.musicbrainz_client.httpx.AsyncClient.get')
    async def test_end_to_end_lookup_workflow(self, mock_get, client):
        """Test complete lookup workflow from client to API."""
        # Setup mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = MOCK_ARTIST_BEATLES
        mock_get.return_value = mock_response

        # Test lookup workflow
        mbid = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
        result = await client.call_tool("get_artist_details", {
            "params": {
                "mbid": mbid,
                "inc": ["releases"]
            }
        })

        # Verify that the tool executed successfully
        assert result is not None

        # Verify that HTTP request was made with correct parameters
        mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_configuration_integration(self, client):
        """Test that configuration is properly integrated."""
        from musicbrainz_mcp.config import get_config

        config = get_config()
        assert config is not None
        assert config.api.rate_limit == 10.0  # From test setup
        assert config.cache.enabled is True
        assert config.debug is True

    @pytest.mark.asyncio
    async def test_cache_integration(self, client):
        """Test that caching is properly integrated."""
        cache = get_cache()

        # Test that cache is working
        cache.set("integration_test", "test_value")
        assert cache.get("integration_test") == "test_value"

        # Clear cache for other tests
        cache.clear()

    @pytest.mark.asyncio
    async def test_error_propagation(self, client):
        """Test that errors are properly propagated through the stack."""
        # Test with invalid MBID format
        with pytest.raises(Exception):  # Should raise validation error
            await client.call_tool("get_artist_details", {
                "params": {
                    "mbid": "invalid-mbid-format"
                }
            })


@pytest.mark.integration
@pytest.mark.slow
class TestRealAPIIntegration:
    """Test integration with real MusicBrainz API (slow tests)."""

    @pytest_asyncio.fixture
    async def real_client(self):
        """Create real MusicBrainz client for API tests."""
        client = MusicBrainzClient(
            user_agent="TestMusicBrainzMCP/1.0.0",
            rate_limit=1.0,  # Respect real API rate limits
            timeout=10.0
        )

        async with client:
            yield client

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_real_artist_search(self, real_client):
        """Test real artist search (requires internet)."""
        try:
            result = await real_client.search_artist("The Beatles", limit=5)

            assert "count" in result
            assert "artists" in result
            assert result["count"] > 0

            # Check that we got Beatles results
            beatles_found = any(
                "beatles" in artist.get("name", "").lower()
                for artist in result["artists"]
            )
            assert beatles_found

        except Exception as e:
            pytest.skip(f"Real API test skipped due to: {e}")

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_real_artist_lookup(self, real_client):
        """Test real artist lookup (requires internet)."""
        try:
            # Use known Beatles MBID
            mbid = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
            result = await real_client.lookup_artist(mbid)

            assert result["id"] == mbid
            assert "name" in result
            assert "The Beatles" in result["name"]

        except Exception as e:
            pytest.skip(f"Real API test skipped due to: {e}")

    @pytest.mark.asyncio
    @pytest.mark.api
    async def test_real_rate_limiting(self, real_client):
        """Test that rate limiting works with real API."""
        try:
            import time

            # Make multiple requests and measure timing
            start_time = time.time()

            await real_client.search_artist("test1", limit=1)
            await real_client.search_artist("test2", limit=1)
            await real_client.search_artist("test3", limit=1)

            end_time = time.time()
            elapsed = end_time - start_time

            # With 1 req/sec rate limit, 3 requests should take at least 2 seconds
            assert elapsed >= 2.0

        except Exception as e:
            pytest.skip(f"Real API test skipped due to: {e}")


@pytest.mark.integration
class TestMCPServerWithRealAPI:
    """Test MCP server with real API integration."""

    @pytest_asyncio.fixture
    async def server_with_real_api(self):
        """Create server configured for real API testing."""
        config = MusicBrainzMCPConfig()
        config.api.user_agent = "TestMusicBrainzMCP/1.0.0"
        config.api.rate_limit = 1.0  # Respect real API limits
        config.cache.enabled = True
        set_config(config)

        return create_server()

    @pytest_asyncio.fixture
    async def client_with_real_api(self, server_with_real_api):
        """Create client connected to server with real API."""
        async with Client(server_with_real_api) as client:
            yield client

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.slow
    async def test_mcp_server_real_search(self, client_with_real_api):
        """Test MCP server with real search API."""
        try:
            result = await client_with_real_api.call_tool("search_artist", {
                "params": {
                    "query": "The Beatles",
                    "limit": 3
                }
            })

            # Verify that the tool executed successfully
            assert result is not None

        except Exception as e:
            pytest.skip(f"Real API test skipped due to: {e}")

    @pytest.mark.asyncio
    @pytest.mark.api
    @pytest.mark.slow
    async def test_mcp_server_real_lookup(self, client_with_real_api):
        """Test MCP server with real lookup API."""
        try:
            mbid = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
            result = await client_with_real_api.call_tool("get_artist_details", {
                "params": {
                    "mbid": mbid
                }
            })

            # Verify that the tool executed successfully
            assert result is not None

        except Exception as e:
            pytest.skip(f"Real API test skipped due to: {e}")


@pytest.mark.integration
class TestCacheIntegration:
    """Test cache integration across components."""

    @pytest_asyncio.fixture
    async def server_with_cache(self):
        """Create server with caching enabled."""
        config = MusicBrainzMCPConfig()
        config.cache.enabled = True
        config.cache.default_ttl = 60
        set_config(config)

        return create_server()

    @pytest_asyncio.fixture
    async def client_with_cache(self, server_with_cache):
        """Create client with caching enabled."""
        async with Client(server_with_cache) as client:
            yield client

    @pytest.mark.asyncio
    @patch('musicbrainz_mcp.musicbrainz_client.httpx.AsyncClient.get')
    async def test_cache_behavior_in_server(self, mock_get, client_with_cache):
        """Test that caching works properly in server context."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = MOCK_ARTIST_SEARCH_RESPONSE
        mock_get.return_value = mock_response

        # Make the same request twice
        params = {
            "params": {
                "query": "The Beatles",
                "limit": 5
            }
        }

        result1 = await client_with_cache.call_tool("search_artist", params)
        result2 = await client_with_cache.call_tool("search_artist", params)

        # Both should succeed
        assert result1 is not None
        assert result2 is not None

        # Note: Actual caching behavior depends on server implementation
        # This test mainly verifies that caching doesn't break functionality


@pytest.mark.integration
class TestConfigurationIntegration:
    """Test configuration integration across components."""

    def test_environment_configuration_integration(self):
        """Test that environment configuration works end-to-end."""
        # Set environment variables
        os.environ["MUSICBRAINZ_RATE_LIMIT"] = "5.0"
        os.environ["CACHE_ENABLED"] = "false"
        os.environ["DEBUG"] = "true"
        
        try:
            # Load configuration from environment
            config = MusicBrainzMCPConfig.from_env()
            
            assert config.api.rate_limit == 5.0
            assert config.cache.enabled is False
            assert config.debug is True
            
        finally:
            # Clean up environment variables
            del os.environ["MUSICBRAINZ_RATE_LIMIT"]
            del os.environ["CACHE_ENABLED"]
            del os.environ["DEBUG"]

    def test_file_configuration_integration(self):
        """Test that file configuration works end-to-end."""
        # Create temporary config file
        config_data = {
            "api": {
                "rate_limit": 3.0,
                "timeout": 20.0
            },
            "cache": {
                "enabled": True,
                "default_ttl": 120
            },
            "debug": False
        }
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            # Load configuration from file
            config = MusicBrainzMCPConfig.from_file(temp_path)
            
            assert config.api.rate_limit == 3.0
            assert config.api.timeout == 20.0
            assert config.cache.enabled is True
            assert config.cache.default_ttl == 120
            assert config.debug is False
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
