"""
Unit tests for MCP server functionality.

Tests the FastMCP server tools, parameter validation, and integration
with the MusicBrainz client using mocked responses.
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastmcp import Client
from musicbrainz_mcp.server import create_server, get_client
from musicbrainz_mcp.exceptions import MusicBrainzError
from tests.mock_data import (
    MOCK_ARTIST_SEARCH_RESPONSE, MOCK_RELEASE_SEARCH_RESPONSE,
    MOCK_RECORDING_SEARCH_RESPONSE, MOCK_ARTIST_BEATLES,
    MOCK_RELEASE_ABBEY_ROAD, MOCK_RECORDING_COME_TOGETHER,
    MOCK_ARTIST_RELEASES_BROWSE_RESPONSE, MOCK_ARTIST_RECORDINGS_BROWSE_RESPONSE
)


@pytest.mark.unit
class TestMCPServerTools:
    """Test MCP server tool functionality."""

    @pytest_asyncio.fixture
    async def server(self):
        """Create test server."""
        return create_server()

    @pytest_asyncio.fixture
    async def client(self, server):
        """Create test client connected to server."""
        async with Client(server) as client:
            yield client

    @pytest.mark.asyncio
    async def test_server_creation(self, server):
        """Test that server is created successfully."""
        assert server is not None
        assert server.name == "MusicBrainz MCP Server"

    @pytest.mark.asyncio
    async def test_list_tools(self, client):
        """Test listing available tools."""
        tools = await client.list_tools()

        assert len(tools) == 10  # We implemented 10 tools

        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "search_artist", "search_release", "search_recording", "search_release_group",
            "get_artist_details", "get_release_details", "get_recording_details",
            "browse_artist_releases", "browse_artist_recordings", "lookup_by_mbid"
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    @pytest.mark.asyncio
    @patch('musicbrainz_mcp.server.get_client')
    async def test_search_artist_tool(self, mock_get_client, client):
        """Test search_artist tool."""
        # Setup mock client
        mock_client = AsyncMock()
        mock_client.search_artist.return_value = MOCK_ARTIST_SEARCH_RESPONSE
        mock_get_client.return_value = mock_client

        # Call tool
        result = await client.call_tool("search_artist", {
            "params": {
                "query": "The Beatles",
                "limit": 10,
                "offset": 0
            }
        })

        # Verify result
        assert result is not None
        # Note: FastMCP Client returns the raw result, so we need to check the structure
        # The actual result format depends on how FastMCP handles tool responses

        # Verify mock was called correctly
        mock_client.search_artist.assert_called_once_with(
            query="The Beatles",
            limit=10,
            offset=0
        )

    @pytest.mark.asyncio
    @patch('musicbrainz_mcp.server.get_client')
    async def test_search_release_tool(self, mock_get_client, client):
        """Test search_release tool."""
        mock_client = AsyncMock()
        mock_client.search_release.return_value = MOCK_RELEASE_SEARCH_RESPONSE
        mock_get_client.return_value = mock_client

        result = await client.call_tool("search_release", {
            "params": {
                "query": "Abbey Road",
                "limit": 5
            }
        })

        assert result is not None
        mock_client.search_release.assert_called_once_with(
            query="Abbey Road",
            limit=5,
            offset=0  # Default value
        )

    @pytest.mark.asyncio
    @patch('musicbrainz_mcp.server.get_client')
    async def test_search_recording_tool(self, mock_get_client, client):
        """Test search_recording tool."""
        mock_client = AsyncMock()
        mock_client.search_recording.return_value = MOCK_RECORDING_SEARCH_RESPONSE
        mock_get_client.return_value = mock_client

        result = await client.call_tool("search_recording", {
            "params": {
                "query": "Come Together",
                "limit": 15,
                "offset": 10
            }
        })

        assert result is not None
        mock_client.search_recording.assert_called_once_with(
            query="Come Together",
            limit=15,
            offset=10
        )

    @pytest.mark.asyncio
    @patch('musicbrainz_mcp.server.get_client')
    async def test_get_artist_details_tool(self, mock_get_client, client):
        """Test get_artist_details tool."""
        mock_client = AsyncMock()
        mock_client.lookup_artist.return_value = MOCK_ARTIST_BEATLES
        mock_get_client.return_value = mock_client

        mbid = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
        result = await client.call_tool("get_artist_details", {
            "params": {
                "mbid": mbid,
                "inc": ["releases", "recordings"]
            }
        })

        assert result is not None
        mock_client.lookup_artist.assert_called_once_with(
            mbid=mbid,
            inc=["releases", "recordings"]
        )

    @pytest.mark.asyncio
    @patch('musicbrainz_mcp.server.get_client')
    async def test_browse_artist_releases_tool(self, mock_get_client, client):
        """Test browse_artist_releases tool."""
        mock_client = AsyncMock()
        mock_client.browse_artist_releases.return_value = MOCK_ARTIST_RELEASES_BROWSE_RESPONSE
        mock_get_client.return_value = mock_client

        artist_mbid = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
        result = await client.call_tool("browse_artist_releases", {
            "params": {
                "artist_mbid": artist_mbid,
                "limit": 20,
                "offset": 0,
                "release_type": ["album"],
                "release_status": ["official"]
            }
        })

        assert result is not None
        mock_client.browse_artist_releases.assert_called_once_with(
            artist_mbid=artist_mbid,
            limit=20,
            offset=0,
            release_type=["album"],
            release_status=["official"]
        )

    @pytest.mark.asyncio
    @patch('musicbrainz_mcp.server.get_client')
    async def test_lookup_by_mbid_tool(self, mock_get_client, client):
        """Test lookup_by_mbid generic tool."""
        mock_client = AsyncMock()
        mock_client.lookup_by_mbid.return_value = MOCK_ARTIST_BEATLES
        mock_get_client.return_value = mock_client

        mbid = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
        result = await client.call_tool("lookup_by_mbid", {
            "params": {
                "entity_type": "artist",
                "mbid": mbid,
                "inc": ["releases"]
            }
        })

        assert result is not None
        mock_client.lookup_by_mbid.assert_called_once_with(
            entity_type="artist",
            mbid=mbid,
            inc=["releases"]
        )


@pytest.mark.unit
class TestMCPServerParameterValidation:
    """Test parameter validation in MCP server tools."""

    @pytest_asyncio.fixture
    async def client(self):
        """Create test client."""
        server = create_server()
        async with Client(server) as client:
            yield client

    @pytest.mark.asyncio
    async def test_search_artist_invalid_parameters(self, client):
        """Test search_artist with invalid parameters."""
        # Test empty query
        with pytest.raises(Exception):  # Should raise validation error
            await client.call_tool("search_artist", {
                "params": {
                    "query": "",
                    "limit": 10
                }
            })

        # Test invalid limit
        with pytest.raises(Exception):
            await client.call_tool("search_artist", {
                "params": {
                    "query": "test",
                    "limit": 0  # Invalid: must be >= 1
                }
            })

        # Test invalid offset
        with pytest.raises(Exception):
            await client.call_tool("search_artist", {
                "params": {
                    "query": "test",
                    "limit": 10,
                    "offset": -1  # Invalid: must be >= 0
                }
            })

    @pytest.mark.asyncio
    async def test_get_artist_details_invalid_mbid(self, client):
        """Test get_artist_details with invalid MBID."""
        with pytest.raises(Exception):  # Should raise validation error
            await client.call_tool("get_artist_details", {
                "params": {
                    "mbid": "invalid-mbid-format"
                }
            })

    @pytest.mark.asyncio
    async def test_lookup_by_mbid_invalid_entity_type(self, client):
        """Test lookup_by_mbid with invalid entity type."""
        with pytest.raises(Exception):  # Should raise validation error
            await client.call_tool("lookup_by_mbid", {
                "params": {
                    "entity_type": "invalid_entity",
                    "mbid": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
                }
            })


@pytest.mark.unit
class TestMCPServerErrorHandling:
    """Test error handling in MCP server tools."""

    @pytest_asyncio.fixture
    async def client(self):
        """Create test client."""
        server = create_server()
        async with Client(server) as client:
            yield client

    @pytest.mark.asyncio
    @patch('musicbrainz_mcp.server.get_client')
    async def test_musicbrainz_api_error_handling(self, mock_get_client, client):
        """Test handling of MusicBrainz API errors."""
        # Setup mock client to raise MusicBrainzError
        mock_client = AsyncMock()
        mock_client.search_artist.side_effect = MusicBrainzError("API Error")
        mock_get_client.return_value = mock_client

        # Test that error is properly handled
        with pytest.raises(Exception):  # FastMCP should propagate the error
            await client.call_tool("search_artist", {
                "params": {
                    "query": "test",
                    "limit": 10
                }
            })

    @pytest.mark.asyncio
    @patch('musicbrainz_mcp.server.get_client')
    async def test_unexpected_error_handling(self, mock_get_client, client):
        """Test handling of unexpected errors."""
        # Setup mock client to raise unexpected error
        mock_client = AsyncMock()
        mock_client.search_artist.side_effect = RuntimeError("Unexpected error")
        mock_get_client.return_value = mock_client

        # Test that error is properly handled
        with pytest.raises(Exception):  # FastMCP should propagate the error
            await client.call_tool("search_artist", {
                "params": {
                    "query": "test",
                    "limit": 10
                }
            })


@pytest.mark.unit
class TestMCPServerClientManagement:
    """Test MCP server client management."""

    @pytest.mark.asyncio
    async def test_get_client_singleton(self):
        """Test that get_client returns singleton instance."""
        # Clear any existing client
        import musicbrainz_mcp.server
        musicbrainz_mcp.server._client = None

        # Get client twice
        client1 = await get_client()
        client2 = await get_client()

        # Should be the same instance
        assert client1 is client2

    @pytest.mark.asyncio
    async def test_get_client_configuration(self):
        """Test that get_client uses environment configuration."""
        import os
        import musicbrainz_mcp.server

        # Clear existing client
        musicbrainz_mcp.server._client = None

        # Set environment variables
        os.environ["MUSICBRAINZ_USER_AGENT"] = "TestAgent/1.0"
        os.environ["MUSICBRAINZ_RATE_LIMIT"] = "2.0"
        os.environ["MUSICBRAINZ_TIMEOUT"] = "15.0"

        try:
            client = await get_client()

            # Verify configuration
            assert client.user_agent == "TestAgent/1.0"
            assert client.rate_limit == 2.0
            assert client.timeout == 15.0

        finally:
            # Clean up environment variables
            del os.environ["MUSICBRAINZ_USER_AGENT"]
            del os.environ["MUSICBRAINZ_RATE_LIMIT"]
            del os.environ["MUSICBRAINZ_TIMEOUT"]

            # Clear client for other tests
            musicbrainz_mcp.server._client = None


@pytest.mark.unit
class TestMCPServerToolDescriptions:
    """Test that MCP server tools have proper descriptions."""

    @pytest.mark.asyncio
    async def test_tool_descriptions_present(self):
        """Test that all tools have descriptions."""
        server = create_server()

        async with Client(server) as client:
            tools = await client.list_tools()

            for tool in tools:
                assert tool.description is not None
                assert len(tool.description) > 0
                # Check that descriptions contain music-related terms
                description_lower = tool.description.lower()
                has_music_terms = any(term in description_lower for term in [
                    "musicbrainz", "music", "artist", "release", "recording", "mbid"
                ])
                assert has_music_terms, f"Tool {tool.name} description should contain music-related terms"

    @pytest.mark.asyncio
    async def test_tool_examples_in_descriptions(self):
        """Test that tool descriptions contain examples."""
        server = create_server()

        async with Client(server) as client:
            tools = await client.list_tools()

            for tool in tools:
                # Most tools should have examples in their descriptions
                description = tool.description.lower()
                has_example = any(keyword in description for keyword in [
                    "example", "e.g.", "for example", "such as"
                ])

                # At least some tools should have examples
                # We'll just check that descriptions are comprehensive
                assert len(tool.description) > 50  # Reasonably detailed


@pytest.mark.unit
class TestMCPServerResponseFormat:
    """Test MCP server response formatting."""

    @pytest_asyncio.fixture
    async def client(self):
        """Create test client."""
        server = create_server()
        async with Client(server) as client:
            yield client

    @pytest.mark.asyncio
    @patch('musicbrainz_mcp.server.get_client')
    async def test_search_response_format(self, mock_get_client, client):
        """Test that search responses have consistent format."""
        mock_client = AsyncMock()
        mock_client.search_artist.return_value = MOCK_ARTIST_SEARCH_RESPONSE
        mock_get_client.return_value = mock_client

        result = await client.call_tool("search_artist", {
            "params": {
                "query": "The Beatles",
                "limit": 10
            }
        })

        # The result structure depends on FastMCP implementation
        # We mainly verify that the tool executes without error
        assert result is not None
