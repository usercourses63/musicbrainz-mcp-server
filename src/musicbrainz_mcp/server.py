"""
FastMCP Server for MusicBrainz Database Queries

This module implements the main MCP server using FastMCP framework with tool definitions
for MusicBrainz queries, proper request/response handling, and integration with the
MusicBrainz client.
"""

import asyncio
import base64
import binascii
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

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

# Global configuration from query parameters
_current_config: Optional[Dict[str, Any]] = None

# Track the configuration used to create the current client
_client_config: Optional[Dict[str, Any]] = None

# Server start time for uptime tracking
start_time = time.time()


def parse_config_from_query_params(query_params: Dict[str, str]) -> Dict[str, Any]:
    """
    Parse configuration from query parameters.

    Supports both:
    - Base64-encoded JSON in `config` param (legacy/convenience)
    - Flat query params as per Smithery session-config (e.g., user_agent, rate_limit, timeout)

    Args:
        query_params: Dictionary of query parameters from HTTP request

    Returns:
        Dictionary of parsed configuration values
    """
    # 1) Prefer explicit flat params (Smithery passes these directly)
    cfg: Dict[str, Any] = {}
    if 'user_agent' in query_params:
        cfg['user_agent'] = query_params.get('user_agent')
    if 'rate_limit' in query_params:
        try:
            cfg['rate_limit'] = float(query_params.get('rate_limit'))
        except (TypeError, ValueError):
            logger.warning("Invalid rate_limit provided; ignoring")
    if 'timeout' in query_params:
        try:
            cfg['timeout'] = float(query_params.get('timeout'))
        except (TypeError, ValueError):
            logger.warning("Invalid timeout provided; ignoring")

    # 2) Fallback: base64-encoded JSON in `config`
    config_param = query_params.get('config')
    if config_param:
        try:
            config_data = base64.b64decode(config_param).decode('utf-8')
            parsed_config = json.loads(config_data)
            cfg.update(parsed_config or {})
        except (binascii.Error, json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to parse base64 config param: {e}")

    if cfg:
        logger.debug(f"Parsed configuration from query parameters: {cfg}")
    return cfg


def configure_client_from_env(config: Optional[Dict[str, Any]] = None):
    """
    Configure the MusicBrainz client from environment variables and optional config.

    Args:
        config: Optional configuration dictionary from query parameters
    """
    global _client

    # Get configuration from environment variables (defaults)
    # Use a smithery.ai-friendly default user agent for tool discovery
    default_user_agent = "SmitheryMusicBrainz/1.1.0 (smithery@musicbrainz-mcp.com)"
    user_agent = os.getenv("MUSICBRAINZ_USER_AGENT", default_user_agent)
    rate_limit = float(os.getenv("MUSICBRAINZ_RATE_LIMIT", "1.0"))
    timeout = float(os.getenv("MUSICBRAINZ_TIMEOUT", "30.0"))

    # Override with query parameter configuration if provided
    if config:
        user_agent = config.get("user_agent", user_agent)
        rate_limit = float(config.get("rate_limit", rate_limit))
        timeout = float(config.get("timeout", timeout))

        logger.info(f"Using configuration from query parameters: user_agent={user_agent}")
    else:
        logger.info(f"Using default configuration for tool discovery: user_agent={user_agent}")

    # Always create/update the client with current configuration
    _client = MusicBrainzClient(
        user_agent=user_agent,
        rate_limit=rate_limit,
        timeout=timeout
    )

    return _client


async def get_client(config: Optional[Dict[str, Any]] = None) -> MusicBrainzClient:
    """
    Get or create the global MusicBrainz client instance.

    Args:
        config: Optional configuration dictionary from query parameters
    """
    global _client, _current_config, _client_config

    # Use provided config, or fall back to global config from middleware
    effective_config = config or _current_config

    # Check if we need to recreate the client due to configuration change
    config_changed = (
        _client is not None and
        effective_config != _client_config
    )

    if _client is None or config_changed:
        # Close existing client if it exists
        if _client is not None:
            await _client.close()
            _client = None

        # Create new client with current configuration
        _client = configure_client_from_env(effective_config)
        await _client.__aenter__()

        # Remember the configuration used for this client
        _client_config = effective_config.copy() if effective_config else None

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
    global _client, _client_config
    if _client is not None:
        await _client.close()
        _client = None
        _client_config = None


class ConfigurationMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and parse configuration from query parameters."""

    async def dispatch(self, request: Request, call_next):
        """
        Extract configuration from query parameters and make it available globally.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or endpoint
        """
        global _current_config

        # Extract query parameters
        query_params = dict(request.query_params)

        # Parse configuration if present
        config = parse_config_from_query_params(query_params)

        # Store configuration globally for use by MCP tools
        if config:
            _current_config = config
            logger.debug(f"Configuration middleware set global config: {config}")

        # Store configuration in request state as well
        request.state.config = config

        # Continue to next middleware/endpoint. This middleware only reads query params
        # and does not touch the request body/stream, so it is safe for /mcp streaming.
        response = await call_next(request)
        return response




def create_http_app_for_tests():
    """
    Build a fully configured HTTP app (without binding a socket) for local smoke tests.

    This mirrors the production HTTP setup used in main():
    - FastMCP HTTP app
    - CORS + Configuration middleware
    - Default client initialization
    - Health, test, and tools endpoints
    """
    try:
        # Create base FastMCP app
        from starlette.responses import JSONResponse
        from starlette.routing import Route
        app = mcp.http_app()

        # Default client for discovery
        configure_client_from_env()

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=[
                "mcp-session-id",
                "mcp-protocol-version",
                "x-mcp-server",
                "x-request-id",
            ],
            max_age=86400,
        )

        # Capture config from query params
        app.add_middleware(ConfigurationMiddleware)

        # Define endpoints (duplicated minimally for tests)
        async def health_check(request: Request):
            try:
                health_data = {
                    "status": "healthy",
                    "service": "MusicBrainz MCP Server",
                    "version": "1.1.0",
                    "tools_count": 10,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "uptime_seconds": time.time() - start_time,
                }
                # Quick readiness heuristic
                health_data["tools_available"] = 10
                health_data["ready"] = True
                return JSONResponse(health_data, status_code=200)
            except Exception as e:
                return JSONResponse({
                    "status": "unhealthy",
                    "service": "MusicBrainz MCP Server",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }, status_code=503)

        async def test_tools(request: Request):
            try:
                test_client = await get_client()
                client_info = {
                    "user_agent": getattr(test_client, "user_agent", None),
                    "rate_limit": getattr(test_client, "rate_limit", None),
                    "timeout": getattr(test_client, "timeout", None),
                    "is_configured": test_client is not None,
                }
                return JSONResponse({
                    "status": "success",
                    "message": "MCP tools are functional",
                    "service": "MusicBrainz MCP Server",
                    "version": "1.1.0",
                    "tools_available": [
                        "search_artist", "search_release", "search_recording",
                        "search_release_group", "get_artist_details",
                        "get_release_details", "get_recording_details",
                        "browse_artist_releases", "browse_artist_recordings",
                        "lookup_by_mbid",
                    ],
                    "client_info": client_info,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                })
            except Exception as e:
                return JSONResponse({
                    "status": "error",
                    "message": f"MCP tools test failed: {str(e)}",
                    "service": "MusicBrainz MCP Server",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }, status_code=500)

        async def list_tools_endpoint(request: Request):
            try:
                config = parse_config_from_query_params(dict(request.query_params))
                configure_client_from_env(config)
                await get_client(config)
                tools_info = [
                    {"name": "search_artist", "description": "Search for artists by name or query string", "category": "search"},
                    {"name": "search_release", "description": "Search for releases (albums, singles, etc.) by title", "category": "search"},
                    {"name": "search_recording", "description": "Search for recordings (individual tracks) by title", "category": "search"},
                    {"name": "search_release_group", "description": "Search for release groups by title", "category": "search"},
                    {"name": "get_artist_details", "description": "Get detailed information about a specific artist by MBID", "category": "lookup"},
                    {"name": "get_release_details", "description": "Get detailed information about a specific release by MBID", "category": "lookup"},
                    {"name": "get_recording_details", "description": "Get detailed information about a specific recording by MBID", "category": "lookup"},
                    {"name": "browse_artist_releases", "description": "Browse releases for a specific artist by MBID", "category": "browse"},
                    {"name": "browse_artist_recordings", "description": "Browse recordings for a specific artist by MBID", "category": "browse"},
                    {"name": "lookup_by_mbid", "description": "Generic lookup for any entity type by MBID", "category": "lookup"},
                ]
                return JSONResponse({
                    "status": "success",
                    "service": "MusicBrainz MCP Server",
                    "version": "1.1.0",
                    "tools": tools_info,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                })
            except Exception as e:
                return JSONResponse({
                    "status": "error",
                    "message": f"Tools listing failed: {str(e)}",
                    "service": "MusicBrainz MCP Server",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }, status_code=500)

        # Register routes
        app.routes.append(Route("/health", health_check, methods=["GET"]))
        app.routes.append(Route("/test", test_tools, methods=["GET"]))
        app.routes.append(Route("/tools", list_tools_endpoint, methods=["GET"]))
        return app
    except Exception:
        logger.exception("Failed to build HTTP app for tests")
        raise

def main():
    """
    Main entry point for the MusicBrainz MCP server.

    This function starts the server with the appropriate transport based on environment:
    - HTTP transport for deployment platforms like smithery.ai (when PORT is set)
    - STDIO transport for local development and Claude Desktop integration
    """
    try:
        logger.info("🎵 Starting MusicBrainz MCP Server v1.1.0...")
        logger.info("🔧 Environment check:")
        logger.info(f"   PORT: {os.getenv('PORT', 'Not set')}")
        logger.info(f"   MUSICBRAINZ_USER_AGENT: {os.getenv('MUSICBRAINZ_USER_AGENT', 'Not set')}")
        logger.info(f"   Python version: {sys.version}")

        logger.info("🛠️ Available tools:")
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
            logger.info(f"🌐 Starting HTTP server on port {port}")

            # Validate dependencies before starting
            try:
                import fastmcp
                import httpx
                import starlette
                logger.info(f"✅ Dependencies validated: FastMCP {fastmcp.__version__}")
            except ImportError as e:
                logger.error(f"❌ Missing dependency: {e}")
                raise

            # Setup Starlette app with CORS for cross-origin requests
            logger.info("🔧 Creating FastMCP HTTP app...")
            app = mcp.http_app()
            logger.info("✅ FastMCP HTTP app created successfully")

            # Initialize MusicBrainz client with default configuration for tool discovery
            logger.info("🔧 Initializing MusicBrainz client with default configuration...")
            configure_client_from_env()
            logger.info("✅ MusicBrainz client initialized successfully")

            # Add optional request logging middleware for debugging (disabled by default)
            from starlette.middleware.base import BaseHTTPMiddleware
            from starlette.requests import Request
            from starlette.responses import Response

            class RequestLoggingMiddleware(BaseHTTPMiddleware):
                async def dispatch(self, request: Request, call_next):
                    # Avoid interfering with MCP streamable endpoints
                    if str(request.url.path).startswith("/mcp"):
                        return await call_next(request)
                    if os.getenv("ENABLE_REQUEST_LOGGING") == "1":
                        logger.info(f"🔍 Request: {request.method} {request.url}")
                        logger.info(f"🔍 Headers: {dict(request.headers)}")
                        if request.query_params:
                            logger.info(f"🔍 Query params: {dict(request.query_params)}")
                    response = await call_next(request)
                    if os.getenv("ENABLE_REQUEST_LOGGING") == "1":
                        logger.info(f"🔍 Response status: {response.status_code}")
                    return response

            # Add health check endpoint
            from starlette.responses import JSONResponse
            from starlette.routing import Route

            async def health_check(request):
                """
                Comprehensive health check following MCP best practices.
                Returns 200 for healthy, 503 for not ready.
                """
                try:
                    # Basic liveness check
                    health_data = {
                        "status": "healthy",
                        "service": "MusicBrainz MCP Server",
                        "version": "1.1.0",
                        "tools_count": 10,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "uptime_seconds": time.time() - start_time
                    }

                    # Check if MCP app is accessible (readiness check)
                    try:
                        # Verify that our MCP tools are available
                        tools = [
                            "search_artist", "search_release", "search_recording",
                            "search_release_group", "get_artist_details",
                            "get_release_details", "get_recording_details",
                            "browse_artist_releases", "browse_artist_recordings",
                            "lookup_by_mbid"
                        ]
                        health_data["tools_available"] = len(tools)
                        health_data["ready"] = True

                        return JSONResponse(health_data, status_code=200)
                    except Exception as e:
                        health_data["ready"] = False
                        health_data["error"] = f"MCP tools not ready: {str(e)}"
                        return JSONResponse(health_data, status_code=503)

                except Exception as e:
                    return JSONResponse({
                        "status": "unhealthy",
                        "service": "MusicBrainz MCP Server",
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }, status_code=503)

            # Add test endpoint for smithery.ai tool scanning
            async def test_tools(request):
                """
                Simple test endpoint that verifies MCP tools are working.
                This helps smithery.ai verify the server is functional during scanning.
                """
                try:
                    # Test that we can create a client with default configuration
                    test_client = await get_client()

                    # Test basic client functionality
                    client_info = {
                        "user_agent": test_client.user_agent,
                        "rate_limit": test_client.rate_limit,
                        "timeout": test_client.timeout,
                        "is_configured": test_client is not None
                    }

                    return JSONResponse({
                        "status": "success",
                        "message": "MCP tools are functional",
                        "service": "MusicBrainz MCP Server",
                        "version": "1.1.0",
                        "tools_available": [
                            "search_artist", "search_release", "search_recording",
                            "search_release_group", "get_artist_details",
                            "get_release_details", "get_recording_details",
                            "browse_artist_releases", "browse_artist_recordings",
                            "lookup_by_mbid"
                        ],
                        "client_info": client_info,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    })
                except Exception as e:
                    return JSONResponse({
                        "status": "error",
                        "message": f"MCP tools test failed: {str(e)}",
                        "service": "MusicBrainz MCP Server",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }, status_code=500)

            # Add MCP tools discovery endpoint for smithery.ai
            async def list_tools_endpoint(request):
                """
                Direct tools listing endpoint for smithery.ai scanning.
                This provides tool information without requiring MCP protocol setup.
                """
                try:
                    # Parse configuration from query parameters if provided
                    config = parse_config_from_query_params(dict(request.query_params))
                    logger.info(f"🔍 Tools discovery request with config: {config}")

                    # Configure client with provided or default configuration
                    configure_client_from_env(config)
                    test_client = await get_client(config)

                    tools_info = [
                        {
                            "name": "search_artist",
                            "description": "Search for artists by name or query string",
                            "category": "search"
                        },
                        {
                            "name": "search_release",
                            "description": "Search for releases (albums, singles, etc.) by title",
                            "category": "search"
                        },
                        {
                            "name": "search_recording",
                            "description": "Search for recordings (individual tracks) by title",
                            "category": "search"
                        },
                        {
                            "name": "search_release_group",
                            "description": "Search for release groups by title",
                            "category": "search"
                        },
                        {
                            "name": "get_artist_details",
                            "description": "Get detailed information about a specific artist by MBID",
                            "category": "lookup"
                        },
                        {
                            "name": "get_release_details",
                            "description": "Get detailed information about a specific release by MBID",
                            "category": "lookup"
                        },
                        {
                            "name": "get_recording_details",
                            "description": "Get detailed information about a specific recording by MBID",
                            "category": "lookup"
                        },
                        {
                            "name": "browse_artist_releases",
                            "description": "Browse releases by a specific artist",
                            "category": "browse"
                        },
                        {
                            "name": "browse_artist_recordings",
                            "description": "Browse recordings by a specific artist",
                            "category": "browse"
                        },
                        {
                            "name": "lookup_by_mbid",
                            "description": "Generic lookup method for any entity type by MBID",
                            "category": "lookup"
                        }
                    ]

                    return JSONResponse({
                        "status": "success",
                        "service": "MusicBrainz MCP Server",
                        "version": "1.1.0",
                        "tools_count": len(tools_info),
                        "tools": tools_info,
                        "client_configured": test_client is not None,
                        "config_received": config,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    })
                except Exception as e:
                    logger.error(f"❌ Tools discovery failed: {e}")
                    return JSONResponse({
                        "status": "error",
                        "message": f"Tools discovery failed: {str(e)}",
                        "service": "MusicBrainz MCP Server",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }, status_code=500)

            # Add health route to the app
            app.routes.append(Route("/health", health_check, methods=["GET"]))
            app.routes.append(Route("/test", test_tools, methods=["GET"]))
            app.routes.append(Route("/tools", list_tools_endpoint, methods=["GET"]))

            # Add request logging middleware only when explicitly enabled
            if os.getenv("ENABLE_REQUEST_LOGGING") == "1":
                app.add_middleware(RequestLoggingMiddleware)

            # Add CORS middleware for browser-based clients
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["*"],
                expose_headers=[
                    "mcp-session-id",
                    "mcp-protocol-version",
                    "x-mcp-server",
                    "x-request-id",
                    "content-length",
                    "content-type"
                ],
                max_age=86400,
            )

            # Add configuration middleware to parse query parameters
            app.add_middleware(ConfigurationMiddleware)

            # Configure uvicorn with proper settings for container deployment
            config = uvicorn.Config(
                app=app,
                host="0.0.0.0",
                port=int(port),
                log_level="info",
                access_log=True,
                server_header=False,
                date_header=False,
                loop="asyncio"
            )

            # Create and run server with proper lifecycle management
            server = uvicorn.Server(config)
            logger.info(f"🚀 Server configured for port {port}, starting...")
            logger.info("🔍 Health check will be available at /health")
            logger.info("🔧 MCP endpoint will be available at /mcp")

            try:
                server.run()
            except Exception as e:
                logger.error(f"❌ Server startup failed: {e}")
                raise
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
