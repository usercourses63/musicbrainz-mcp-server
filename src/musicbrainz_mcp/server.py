"""
FastMCP Server for MusicBrainz Database Queries

This module implements the main MCP server using FastMCP framework with tool definitions
for MusicBrainz queries, proper request/response handling, and integration with the
MusicBrainz client.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import uvicorn
from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

from .musicbrainz_client import MusicBrainzClient
from .models import Artist, Release, Recording, ReleaseGroup, SearchResult, BrowseResult
from .schemas import ResponseParser, ValidationHelpers
from .exceptions import MusicBrainzError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastMCP server instance
mcp = FastMCP("MusicBrainz MCP Server")

# Global MusicBrainz client instance
_client: Optional[MusicBrainzClient] = None


def configure_client_from_env():
    """Configure the MusicBrainz client from environment variables and query parameters."""
    global _client

    # Get configuration from environment variables
    user_agent = os.getenv("MUSICBRAINZ_USER_AGENT", "MusicBrainzMCP/1.0.0")
    rate_limit = float(os.getenv("MUSICBRAINZ_RATE_LIMIT", "1.0"))
    timeout = float(os.getenv("MUSICBRAINZ_TIMEOUT", "30.0"))

    # For HTTP mode, configuration might come from query parameters
    # This will be handled by the FastMCP framework automatically

    if _client is None:
        _client = MusicBrainzClient(
            user_agent=user_agent,
            rate_limit=rate_limit,
            timeout=timeout
        )

    return _client


async def get_client() -> MusicBrainzClient:
    """Get or create the global MusicBrainz client instance."""
    global _client
    if _client is None:
        _client = configure_client_from_env()
        await _client.__aenter__()

    return _client


# Pydantic models for tool parameters
class SearchParams(BaseModel):
    """Parameters for search operations."""
    query: str = Field(..., description="Search query string")
    limit: int = Field(25, description="Maximum number of results (1-100)", ge=1, le=100)
    offset: int = Field(0, description="Offset for pagination", ge=0)


class LookupParams(BaseModel):
    """Parameters for lookup operations."""
    mbid: str = Field(..., description="MusicBrainz ID (UUID format)")
    inc: Optional[List[str]] = Field(None, description="Additional data to include")


class BrowseParams(BaseModel):
    """Parameters for browse operations."""
    artist_mbid: str = Field(..., description="MusicBrainz ID of the artist")
    limit: int = Field(25, description="Maximum number of results (1-100)", ge=1, le=100)
    offset: int = Field(0, description="Offset for pagination", ge=0)
    release_type: Optional[List[str]] = Field(None, description="Filter by release type")
    release_status: Optional[List[str]] = Field(None, description="Filter by release status")


class GenericLookupParams(BaseModel):
    """Parameters for generic lookup operations."""
    entity_type: str = Field(..., description="Type of entity (artist, release, recording, etc.)")
    mbid: str = Field(..., description="MusicBrainz ID (UUID format)")
    inc: Optional[List[str]] = Field(None, description="Additional data to include")


@mcp.tool
async def search_artist(params: SearchParams, ctx: Context) -> Dict[str, Any]:
    """
    Search for artists by name or query string.
    
    This tool searches the MusicBrainz database for artists matching the provided query.
    Results include artist names, MBIDs, types, countries, and other metadata.
    
    Args:
        params: Search parameters including query, limit, and offset
        ctx: MCP context for logging and progress reporting
        
    Returns:
        Search results containing artists and pagination metadata
        
    Example:
        search_artist({"query": "The Beatles", "limit": 10})
    """
    try:
        await ctx.info(f"Searching for artists: '{params.query}'")
        
        client = await get_client()
        results = await client.search_artist(
            query=params.query,
            limit=params.limit,
            offset=params.offset
        )
        
        # Parse results using our response parser
        search_result = ResponseParser.parse_search_response(results, "artist")
        
        await ctx.info(f"Found {search_result.count} artists")
        
        return {
            "count": search_result.count,
            "offset": search_result.offset,
            "artists": [artist.model_dump() for artist in (search_result.artists or [])]
        }
        
    except MusicBrainzError as e:
        await ctx.error(f"MusicBrainz API error: {e}")
        raise
    except Exception as e:
        await ctx.error(f"Unexpected error during artist search: {e}")
        raise


@mcp.tool
async def search_release(params: SearchParams, ctx: Context) -> Dict[str, Any]:
    """
    Search for releases (albums, singles, etc.) by title or query string.
    
    This tool searches the MusicBrainz database for releases matching the provided query.
    Results include release titles, MBIDs, artist credits, dates, and other metadata.
    
    Args:
        params: Search parameters including query, limit, and offset
        ctx: MCP context for logging and progress reporting
        
    Returns:
        Search results containing releases and pagination metadata
        
    Example:
        search_release({"query": "Abbey Road", "limit": 10})
    """
    try:
        await ctx.info(f"Searching for releases: '{params.query}'")
        
        client = await get_client()
        results = await client.search_release(
            query=params.query,
            limit=params.limit,
            offset=params.offset
        )
        
        # Parse results using our response parser
        search_result = ResponseParser.parse_search_response(results, "release")
        
        await ctx.info(f"Found {search_result.count} releases")
        
        return {
            "count": search_result.count,
            "offset": search_result.offset,
            "releases": [release.model_dump() for release in (search_result.releases or [])]
        }
        
    except MusicBrainzError as e:
        await ctx.error(f"MusicBrainz API error: {e}")
        raise
    except Exception as e:
        await ctx.error(f"Unexpected error during release search: {e}")
        raise


@mcp.tool
async def search_recording(params: SearchParams, ctx: Context) -> Dict[str, Any]:
    """
    Search for recordings (individual tracks) by title or query string.
    
    This tool searches the MusicBrainz database for recordings matching the provided query.
    Results include recording titles, MBIDs, artist credits, lengths, and other metadata.
    
    Args:
        params: Search parameters including query, limit, and offset
        ctx: MCP context for logging and progress reporting
        
    Returns:
        Search results containing recordings and pagination metadata
        
    Example:
        search_recording({"query": "Come Together", "limit": 10})
    """
    try:
        await ctx.info(f"Searching for recordings: '{params.query}'")
        
        client = await get_client()
        results = await client.search_recording(
            query=params.query,
            limit=params.limit,
            offset=params.offset
        )
        
        # Parse results using our response parser
        search_result = ResponseParser.parse_search_response(results, "recording")
        
        await ctx.info(f"Found {search_result.count} recordings")
        
        return {
            "count": search_result.count,
            "offset": search_result.offset,
            "recordings": [recording.model_dump() for recording in (search_result.recordings or [])]
        }
        
    except MusicBrainzError as e:
        await ctx.error(f"MusicBrainz API error: {e}")
        raise
    except Exception as e:
        await ctx.error(f"Unexpected error during recording search: {e}")
        raise


@mcp.tool
async def search_release_group(params: SearchParams, ctx: Context) -> Dict[str, Any]:
    """
    Search for release groups by title or query string.
    
    This tool searches the MusicBrainz database for release groups matching the provided query.
    Results include release group titles, MBIDs, artist credits, types, and other metadata.
    
    Args:
        params: Search parameters including query, limit, and offset
        ctx: MCP context for logging and progress reporting
        
    Returns:
        Search results containing release groups and pagination metadata
        
    Example:
        search_release_group({"query": "Sgt. Pepper's Lonely Hearts Club Band", "limit": 10})
    """
    try:
        await ctx.info(f"Searching for release groups: '{params.query}'")
        
        client = await get_client()
        results = await client.search_release_group(
            query=params.query,
            limit=params.limit,
            offset=params.offset
        )
        
        # Parse results using our response parser
        search_result = ResponseParser.parse_search_response(results, "release-group")
        
        await ctx.info(f"Found {search_result.count} release groups")
        
        return {
            "count": search_result.count,
            "offset": search_result.offset,
            "release_groups": [rg.model_dump() for rg in (search_result.release_groups or [])]
        }
        
    except MusicBrainzError as e:
        await ctx.error(f"MusicBrainz API error: {e}")
        raise
    except Exception as e:
        await ctx.error(f"Unexpected error during release group search: {e}")
        raise


@mcp.tool
async def get_artist_details(params: LookupParams, ctx: Context) -> Dict[str, Any]:
    """
    Get detailed information about a specific artist by MBID.

    This tool retrieves comprehensive artist information including biography,
    relationships, aliases, and optionally related releases and recordings.

    Args:
        params: Lookup parameters including MBID and optional includes
        ctx: MCP context for logging and progress reporting

    Returns:
        Detailed artist information

    Example:
        get_artist_details({"mbid": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d", "inc": ["releases", "recordings"]})
    """
    try:
        # Validate MBID format
        if not ValidationHelpers.validate_mbid(params.mbid):
            raise ValueError(f"Invalid MBID format: {params.mbid}")

        await ctx.info(f"Looking up artist details for MBID: {params.mbid}")

        client = await get_client()
        result = await client.lookup_artist(
            mbid=params.mbid,
            inc=params.inc
        )

        # Parse the artist data
        artist = Artist(**result)

        await ctx.info(f"Retrieved details for artist: {artist.name}")

        return artist.model_dump()

    except MusicBrainzError as e:
        await ctx.error(f"MusicBrainz API error: {e}")
        raise
    except Exception as e:
        await ctx.error(f"Unexpected error during artist lookup: {e}")
        raise


@mcp.tool
async def get_release_details(params: LookupParams, ctx: Context) -> Dict[str, Any]:
    """
    Get detailed information about a specific release by MBID.

    This tool retrieves comprehensive release information including track listings,
    artist credits, label information, and cover art details.

    Args:
        params: Lookup parameters including MBID and optional includes
        ctx: MCP context for logging and progress reporting

    Returns:
        Detailed release information

    Example:
        get_release_details({"mbid": "f4a261d1-2a31-4d1a-b4b6-7d6e4c8f9a0b", "inc": ["recordings", "artist-credits"]})
    """
    try:
        # Validate MBID format
        if not ValidationHelpers.validate_mbid(params.mbid):
            raise ValueError(f"Invalid MBID format: {params.mbid}")

        await ctx.info(f"Looking up release details for MBID: {params.mbid}")

        client = await get_client()
        result = await client.lookup_release(
            mbid=params.mbid,
            inc=params.inc
        )

        # Parse the release data
        release = Release(**result)

        await ctx.info(f"Retrieved details for release: {release.title}")

        return release.model_dump()

    except MusicBrainzError as e:
        await ctx.error(f"MusicBrainz API error: {e}")
        raise
    except Exception as e:
        await ctx.error(f"Unexpected error during release lookup: {e}")
        raise


@mcp.tool
async def get_recording_details(params: LookupParams, ctx: Context) -> Dict[str, Any]:
    """
    Get detailed information about a specific recording by MBID.

    This tool retrieves comprehensive recording information including artist credits,
    ISRC codes, relationships, and associated releases.

    Args:
        params: Lookup parameters including MBID and optional includes
        ctx: MCP context for logging and progress reporting

    Returns:
        Detailed recording information

    Example:
        get_recording_details({"mbid": "c1a2b3d4-e5f6-7890-abcd-ef1234567890", "inc": ["releases", "artist-credits"]})
    """
    try:
        # Validate MBID format
        if not ValidationHelpers.validate_mbid(params.mbid):
            raise ValueError(f"Invalid MBID format: {params.mbid}")

        await ctx.info(f"Looking up recording details for MBID: {params.mbid}")

        client = await get_client()
        result = await client.lookup_recording(
            mbid=params.mbid,
            inc=params.inc
        )

        # Parse the recording data
        recording = Recording(**result)

        await ctx.info(f"Retrieved details for recording: {recording.title}")

        return recording.model_dump()

    except MusicBrainzError as e:
        await ctx.error(f"MusicBrainz API error: {e}")
        raise
    except Exception as e:
        await ctx.error(f"Unexpected error during recording lookup: {e}")
        raise


@mcp.tool
async def browse_artist_releases(params: BrowseParams, ctx: Context) -> Dict[str, Any]:
    """
    Browse releases by a specific artist.

    This tool retrieves all releases associated with a specific artist,
    with optional filtering by release type and status.

    Args:
        params: Browse parameters including artist MBID, filters, and pagination
        ctx: MCP context for logging and progress reporting

    Returns:
        Browse results containing releases and pagination metadata

    Example:
        browse_artist_releases({"artist_mbid": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d", "release_type": ["album"], "limit": 20})
    """
    try:
        # Validate MBID format
        if not ValidationHelpers.validate_mbid(params.artist_mbid):
            raise ValueError(f"Invalid MBID format: {params.artist_mbid}")

        await ctx.info(f"Browsing releases for artist MBID: {params.artist_mbid}")

        client = await get_client()
        results = await client.browse_artist_releases(
            artist_mbid=params.artist_mbid,
            limit=params.limit,
            offset=params.offset,
            release_type=params.release_type,
            release_status=params.release_status
        )

        # Parse results using our response parser
        browse_result = ResponseParser.parse_browse_response(results, "release")

        await ctx.info(f"Found {browse_result.count} releases for artist")

        return {
            "count": browse_result.count,
            "offset": browse_result.offset,
            "releases": [release.model_dump() for release in (browse_result.releases or [])]
        }

    except MusicBrainzError as e:
        await ctx.error(f"MusicBrainz API error: {e}")
        raise
    except Exception as e:
        await ctx.error(f"Unexpected error during artist releases browse: {e}")
        raise


@mcp.tool
async def browse_artist_recordings(params: BrowseParams, ctx: Context) -> Dict[str, Any]:
    """
    Browse recordings by a specific artist.

    This tool retrieves all recordings associated with a specific artist,
    useful for finding all tracks by an artist across different releases.

    Args:
        params: Browse parameters including artist MBID and pagination
        ctx: MCP context for logging and progress reporting

    Returns:
        Browse results containing recordings and pagination metadata

    Example:
        browse_artist_recordings({"artist_mbid": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d", "limit": 50})
    """
    try:
        # Validate MBID format
        if not ValidationHelpers.validate_mbid(params.artist_mbid):
            raise ValueError(f"Invalid MBID format: {params.artist_mbid}")

        await ctx.info(f"Browsing recordings for artist MBID: {params.artist_mbid}")

        client = await get_client()
        results = await client.browse_artist_recordings(
            artist_mbid=params.artist_mbid,
            limit=params.limit,
            offset=params.offset
        )

        # Parse results using our response parser
        browse_result = ResponseParser.parse_browse_response(results, "recording")

        await ctx.info(f"Found {browse_result.count} recordings for artist")

        return {
            "count": browse_result.count,
            "offset": browse_result.offset,
            "recordings": [recording.model_dump() for recording in (browse_result.recordings or [])]
        }

    except MusicBrainzError as e:
        await ctx.error(f"MusicBrainz API error: {e}")
        raise
    except Exception as e:
        await ctx.error(f"Unexpected error during artist recordings browse: {e}")
        raise


@mcp.tool
async def lookup_by_mbid(params: GenericLookupParams, ctx: Context) -> Dict[str, Any]:
    """
    Generic lookup method for any entity type by MBID.

    This tool provides a unified interface for looking up any MusicBrainz entity
    (artist, release, recording, release-group, label, work, etc.) by its MBID.

    Args:
        params: Generic lookup parameters including entity type, MBID, and optional includes
        ctx: MCP context for logging and progress reporting

    Returns:
        Entity data based on the specified type

    Example:
        lookup_by_mbid({"entity_type": "artist", "mbid": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d", "inc": ["releases"]})
    """
    try:
        # Validate MBID format
        if not ValidationHelpers.validate_mbid(params.mbid):
            raise ValueError(f"Invalid MBID format: {params.mbid}")

        await ctx.info(f"Looking up {params.entity_type} with MBID: {params.mbid}")

        client = await get_client()
        result = await client.lookup_by_mbid(
            entity_type=params.entity_type,
            mbid=params.mbid,
            inc=params.inc
        )

        # Parse the entity data using the response parser
        entity = ResponseParser.parse_entity_response(result, params.entity_type)

        await ctx.info(f"Retrieved {params.entity_type} details")

        return entity.model_dump()

    except MusicBrainzError as e:
        await ctx.error(f"MusicBrainz API error: {e}")
        raise
    except Exception as e:
        await ctx.error(f"Unexpected error during {params.entity_type} lookup: {e}")
        raise


def create_server() -> FastMCP:
    """
    Create and configure the MusicBrainz MCP server.

    Returns:
        Configured FastMCP server instance
    """
    return mcp


async def cleanup():
    """Clean up resources when the server shuts down."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None


def main():
    """
    Main entry point for the MusicBrainz MCP server.

    This function starts the server with the appropriate transport based on environment:
    - HTTP transport for deployment platforms like smithery.ai (when PORT is set)
    - STDIO transport for local development and Claude Desktop integration
    """
    try:
        logger.info("Starting MusicBrainz MCP Server...")
        logger.info("Available tools:")
        logger.info("  - search_artist: Search for artists by name")
        logger.info("  - search_release: Search for releases/albums")
        logger.info("  - search_recording: Search for recordings/tracks")
        logger.info("  - search_release_group: Search for release groups")
        logger.info("  - get_artist_details: Get detailed artist information")
        logger.info("  - get_release_details: Get detailed release information")
        logger.info("  - get_recording_details: Get detailed recording information")
        logger.info("  - browse_artist_releases: Browse releases by artist")
        logger.info("  - browse_artist_recordings: Browse recordings by artist")
        logger.info("  - lookup_by_mbid: Generic lookup by MBID")

        # Check if we should use HTTP transport (for deployment platforms)
        port = os.getenv("PORT")
        if port:
            # HTTP transport for deployment platforms like smithery.ai
            logger.info(f"Starting HTTP server on port {port}")

            # Setup Starlette app with CORS for cross-origin requests
            app = mcp.streamable_http_app()

            # Add health check endpoint
            from starlette.responses import JSONResponse

            @app.route("/health", methods=["GET"])
            async def health_check(request):
                return JSONResponse({"status": "healthy", "service": "MusicBrainz MCP Server"})

            # Add CORS middleware for browser-based clients
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["*"],
                expose_headers=["mcp-session-id", "mcp-protocol-version"],
                max_age=86400,
            )

            # Run with uvicorn
            uvicorn.run(app, host="0.0.0.0", port=int(port), log_level="info")
        else:
            # STDIO transport for local development and Claude Desktop
            logger.info("Starting with STDIO transport")
            mcp.run()

    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        # Clean up resources
        asyncio.run(cleanup())


if __name__ == "__main__":
    main()
