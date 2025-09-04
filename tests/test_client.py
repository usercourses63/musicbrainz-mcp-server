"""
Unit tests for MusicBrainz API client.

Tests the MusicBrainzClient class with mocked HTTP responses to ensure
proper API interaction, error handling, and rate limiting.
"""

import pytest
import pytest_asyncio
import asyncio
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from musicbrainz_mcp.musicbrainz_client import MusicBrainzClient
from musicbrainz_mcp.exceptions import (
    MusicBrainzError, MusicBrainzRateLimitError, MusicBrainzNotFoundError,
    MusicBrainzValidationError
)
from tests.mock_data import (
    MOCK_ARTIST_BEATLES, MOCK_ARTIST_SEARCH_RESPONSE,
    MOCK_RELEASE_ABBEY_ROAD, MOCK_RELEASE_SEARCH_RESPONSE,
    MOCK_RECORDING_COME_TOGETHER, MOCK_RECORDING_SEARCH_RESPONSE,
    MOCK_ARTIST_RELEASES_BROWSE_RESPONSE, MOCK_ERROR_RESPONSE_404,
    MOCK_RATE_LIMIT_RESPONSE
)


@pytest.mark.unit
class TestMusicBrainzClient:
    """Test cases for MusicBrainzClient."""

    @pytest_asyncio.fixture
    async def client(self):
        """Create a test client."""
        client = MusicBrainzClient(
            user_agent="TestMusicBrainzMCP/1.0.0",
            rate_limit=10.0,
            timeout=5.0
        )
        async with client:
            yield client

    @pytest.fixture
    def mock_response(self):
        """Create a mock HTTP response."""
        response = AsyncMock()
        response.status_code = 200
        response.headers = {"Content-Type": "application/json"}
        response.raise_for_status = MagicMock()
        return response

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization with default parameters."""
        client = MusicBrainzClient()
        assert client.user_agent.startswith("MusicBrainzMCP/")
        assert client.rate_limit == 1.0
        assert client.timeout == 30.0

    @pytest.mark.asyncio
    async def test_client_custom_parameters(self):
        """Test client initialization with custom parameters."""
        client = MusicBrainzClient(
            user_agent="CustomAgent/2.0",
            rate_limit=2.5,
            timeout=15.0
        )
        assert client.user_agent == "CustomAgent/2.0"
        assert client.rate_limit == 2.5
        assert client.timeout == 15.0

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test client as async context manager."""
        client = MusicBrainzClient()

        async with client:
            assert client._client is not None
            assert isinstance(client._client, httpx.AsyncClient)

        # Session should be closed after context exit
        assert client._client is None

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_search_artist_success(self, mock_get, client):
        """Test successful artist search."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = MOCK_ARTIST_SEARCH_RESPONSE
        mock_get.return_value = mock_response

        # Test search
        result = await client.search_artist("The Beatles", limit=25, offset=0)

        # Verify result
        assert result == MOCK_ARTIST_SEARCH_RESPONSE
        assert result["count"] == 177437
        assert len(result["artists"]) == 2
        assert result["artists"][0]["name"] == "The Beatles"

        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "artist" in call_args[0][0]  # URL contains 'artist'

        # Check query parameters
        params = call_args.kwargs.get('params', {})
        assert params['query'] == "The Beatles"
        assert params['limit'] == 25
        assert params['offset'] == 0

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_lookup_artist_success(self, mock_get, client):
        """Test successful artist lookup."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = MOCK_ARTIST_BEATLES
        mock_get.return_value = mock_response

        # Test lookup
        mbid = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
        result = await client.lookup_artist(mbid)

        # Verify result
        assert result == MOCK_ARTIST_BEATLES
        assert result["id"] == mbid
        assert result["name"] == "The Beatles"

        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert mbid in call_args[0][0]  # URL contains MBID

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_search_release_success(self, mock_get, client):
        """Test successful release search."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = MOCK_RELEASE_SEARCH_RESPONSE
        mock_get.return_value = mock_response

        result = await client.search_release("Abbey Road")

        assert result == MOCK_RELEASE_SEARCH_RESPONSE
        assert result["count"] == 1234
        assert result["releases"][0]["title"] == "Abbey Road"

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_search_recording_success(self, mock_get, client):
        """Test successful recording search."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = MOCK_RECORDING_SEARCH_RESPONSE
        mock_get.return_value = mock_response

        result = await client.search_recording("Come Together")

        assert result == MOCK_RECORDING_SEARCH_RESPONSE
        assert result["count"] == 567
        assert result["recordings"][0]["title"] == "Come Together"

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_browse_artist_releases_success(self, mock_get, client):
        """Test successful browse artist releases."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = MOCK_ARTIST_RELEASES_BROWSE_RESPONSE
        mock_get.return_value = mock_response

        artist_mbid = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
        result = await client.browse_artist_releases(artist_mbid)

        assert result == MOCK_ARTIST_RELEASES_BROWSE_RESPONSE
        assert result["release-count"] == 3106
        assert len(result["releases"]) == 2

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_http_404_error(self, mock_get, client):
        """Test handling of 404 Not Found errors."""
        # Setup mock response for 404
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.is_success = False
        mock_response.json.return_value = MOCK_ERROR_RESPONSE_404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=mock_response
        )
        mock_get.return_value = mock_response

        # Test that MusicBrainzNotFoundError is raised
        with pytest.raises(MusicBrainzNotFoundError):
            await client.lookup_artist("b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d")

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_rate_limit_error(self, mock_get, client):
        """Test handling of rate limit errors."""
        # Setup mock response for rate limit
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.is_success = False
        mock_response.json.return_value = MOCK_RATE_LIMIT_RESPONSE
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "503 Service Unavailable", request=MagicMock(), response=mock_response
        )
        mock_get.return_value = mock_response

        # Test that MusicBrainzRateLimitError is raised
        with pytest.raises(MusicBrainzRateLimitError):
            await client.search_artist("test")

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_generic_http_error(self, mock_get, client):
        """Test handling of generic HTTP errors."""
        # Setup mock response for 500 error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.is_success = False
        mock_response.json.return_value = {"error": "Internal Server Error"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error", request=MagicMock(), response=mock_response
        )
        mock_get.return_value = mock_response

        # Test that MusicBrainzError is raised
        with pytest.raises(MusicBrainzError):
            await client.search_artist("test")

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_network_timeout(self, mock_get, client):
        """Test handling of network timeouts."""
        # Setup mock to raise timeout
        mock_get.side_effect = httpx.TimeoutException("Request timed out")

        # Test that MusicBrainzError is raised
        with pytest.raises(MusicBrainzError) as exc_info:
            await client.search_artist("test")

        assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_network_connection_error(self, mock_get, client):
        """Test handling of network connection errors."""
        # Setup mock to raise connection error
        mock_get.side_effect = httpx.ConnectError("Connection failed")

        # Test that MusicBrainzError is raised
        with pytest.raises(MusicBrainzError) as exc_info:
            await client.search_artist("test")

        assert "connection" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_rate_limiting_delay(self, client):
        """Test that rate limiting introduces appropriate delays."""
        # Set a high rate limit for testing
        client.rate_limit = 100.0  # 100 requests per second

        # Mock the HTTP call to return immediately
        with patch.object(client._client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.is_success = True
            mock_response.json.return_value = MOCK_ARTIST_SEARCH_RESPONSE
            mock_get.return_value = mock_response

            # Make multiple requests and measure timing
            import time
            start_time = time.time()

            await client.search_artist("test1")
            await client.search_artist("test2")

            end_time = time.time()
            elapsed = end_time - start_time

            # Should have some delay due to rate limiting
            # With 100 req/sec, minimum delay between requests is 0.01 seconds
            assert elapsed >= 0.01

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_include_parameters(self, mock_get, client):
        """Test that include parameters are properly formatted."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = MOCK_ARTIST_BEATLES
        mock_get.return_value = mock_response

        # Test lookup with include parameters
        mbid = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
        inc = ["releases", "recordings", "release-groups"]

        await client.lookup_artist(mbid, inc=inc)

        # Verify that inc parameter is properly formatted
        mock_get.assert_called_once()
        call_args = mock_get.call_args

        # Check query parameters
        params = call_args.kwargs.get('params', {})
        assert 'inc' in params
        assert params['inc'] == "releases+recordings+release-groups"

    @pytest.mark.asyncio
    async def test_invalid_parameters(self, client):
        """Test handling of invalid parameters."""
        # Test invalid limit
        with pytest.raises(MusicBrainzValidationError):
            await client.search_artist("test", limit=0)

        with pytest.raises(MusicBrainzValidationError):
            await client.search_artist("test", limit=101)

        # Test invalid offset
        with pytest.raises(MusicBrainzValidationError):
            await client.search_artist("test", offset=-1)

    @pytest.mark.asyncio
    async def test_empty_query_handling(self, client):
        """Test handling of empty search queries."""
        with pytest.raises(MusicBrainzValidationError):
            await client.search_artist("")

        with pytest.raises(MusicBrainzValidationError):
            await client.search_artist("   ")  # Only whitespace
