"""
MusicBrainz API Client

This module provides an async HTTP client for interacting with the MusicBrainz API.
It includes rate limiting, error handling, and support for all major entity types.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import httpx

from .exceptions import (
    MusicBrainzAPIError,
    MusicBrainzBadRequestError,
    MusicBrainzConnectionError,
    MusicBrainzNotFoundError,
    MusicBrainzRateLimitError,
    MusicBrainzTimeoutError,
    MusicBrainzValidationError,
)

logger = logging.getLogger(__name__)


class MusicBrainzClient:
    """
    Async HTTP client for the MusicBrainz API.
    
    This client handles rate limiting, error handling, and provides methods
    for searching and looking up various MusicBrainz entities.
    """

    BASE_URL = "https://musicbrainz.org/ws/2"
    DEFAULT_USER_AGENT = "MusicBrainzMCP/0.1.0 (https://github.com/yourusername/musicbrainz-mcp)"
    DEFAULT_RATE_LIMIT = 1.0  # 1 request per second
    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        user_agent: Optional[str] = None,
        rate_limit: float = DEFAULT_RATE_LIMIT,
        timeout: float = DEFAULT_TIMEOUT,
        base_url: Optional[str] = None,
    ) -> None:
        """
        Initialize the MusicBrainz client.

        Args:
            user_agent: Custom User-Agent string. If None, uses default.
            rate_limit: Rate limit in requests per second (default: 1.0).
            timeout: Request timeout in seconds (default: 30.0).
            base_url: Base URL for the API (default: MusicBrainz production).
        """
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.base_url = base_url or self.BASE_URL
        
        # Rate limiting state
        self._last_request_time = 0.0
        self._rate_limit_lock = asyncio.Lock()
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "MusicBrainzClient":
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self) -> None:
        """Ensure the HTTP client is initialized."""
        if self._client is None:
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            }
            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
            )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _rate_limit(self) -> None:
        """Enforce rate limiting."""
        async with self._rate_limit_lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            min_interval = 1.0 / self.rate_limit
            
            if time_since_last < min_interval:
                sleep_time = min_interval - time_since_last
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
            
            self._last_request_time = time.time()

    def _validate_mbid(self, mbid: str) -> None:
        """Validate that a string is a valid MBID (UUID format)."""
        import re
        
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE
        )
        
        if not uuid_pattern.match(mbid):
            raise MusicBrainzValidationError(f"Invalid MBID format: {mbid}")

    def _handle_http_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses."""
        status_code = response.status_code
        response_text = response.text
        
        if status_code == 400:
            raise MusicBrainzBadRequestError(f"Bad request: {response_text}")
        elif status_code == 404:
            raise MusicBrainzNotFoundError(f"Resource not found: {response_text}")
        elif status_code == 503:
            # Extract retry-after header if present
            retry_after = response.headers.get("Retry-After")
            retry_seconds = int(retry_after) if retry_after else None
            raise MusicBrainzRateLimitError(
                "Rate limit exceeded", retry_after=retry_seconds
            )
        else:
            raise MusicBrainzAPIError(
                f"HTTP {status_code} error", status_code, response_text
            )

    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the MusicBrainz API.

        Args:
            endpoint: API endpoint (e.g., "artist/search").
            params: Query parameters.

        Returns:
            JSON response data.

        Raises:
            Various MusicBrainzError subclasses for different error conditions.
        """
        await self._ensure_client()
        await self._rate_limit()
        
        # Ensure JSON format
        if params is None:
            params = {}
        params["fmt"] = "json"
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            logger.debug(f"Making request to {url} with params: {params}")
            
            response = await self._client.get(url, params=params)
            
            if not response.is_success:
                self._handle_http_error(response)
            
            return response.json()
            
        except httpx.TimeoutException as e:
            raise MusicBrainzTimeoutError(f"Request timed out: {e}")
        except httpx.ConnectError as e:
            raise MusicBrainzConnectionError(f"Connection error: {e}")
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e.response)
        except Exception as e:
            if isinstance(e, (MusicBrainzAPIError, MusicBrainzValidationError)):
                raise
            raise MusicBrainzAPIError(f"Unexpected error: {e}", status_code=0)

    async def search_artist(
        self,
        query: str,
        limit: int = 25,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Search for artists.

        Args:
            query: Search query string.
            limit: Maximum number of results (default: 25, max: 100).
            offset: Offset for pagination (default: 0).

        Returns:
            Search results containing artists and metadata.
        """
        if not query.strip():
            raise MusicBrainzValidationError("Query cannot be empty")
        
        if limit < 1 or limit > 100:
            raise MusicBrainzValidationError("Limit must be between 1 and 100")
        
        if offset < 0:
            raise MusicBrainzValidationError("Offset must be non-negative")

        params = {
            "query": query,
            "limit": limit,
            "offset": offset,
        }
        
        return await self._make_request("artist", params)

    async def search_release(
        self,
        query: str,
        limit: int = 25,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Search for releases.

        Args:
            query: Search query string.
            limit: Maximum number of results (default: 25, max: 100).
            offset: Offset for pagination (default: 0).

        Returns:
            Search results containing releases and metadata.
        """
        if not query.strip():
            raise MusicBrainzValidationError("Query cannot be empty")
        
        if limit < 1 or limit > 100:
            raise MusicBrainzValidationError("Limit must be between 1 and 100")
        
        if offset < 0:
            raise MusicBrainzValidationError("Offset must be non-negative")

        params = {
            "query": query,
            "limit": limit,
            "offset": offset,
        }
        
        return await self._make_request("release", params)

    async def search_recording(
        self,
        query: str,
        limit: int = 25,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Search for recordings.

        Args:
            query: Search query string.
            limit: Maximum number of results (default: 25, max: 100).
            offset: Offset for pagination (default: 0).

        Returns:
            Search results containing recordings and metadata.
        """
        if not query.strip():
            raise MusicBrainzValidationError("Query cannot be empty")
        
        if limit < 1 or limit > 100:
            raise MusicBrainzValidationError("Limit must be between 1 and 100")
        
        if offset < 0:
            raise MusicBrainzValidationError("Offset must be non-negative")

        params = {
            "query": query,
            "limit": limit,
            "offset": offset,
        }
        
        return await self._make_request("recording", params)

    async def search_release_group(
        self,
        query: str,
        limit: int = 25,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Search for release groups.

        Args:
            query: Search query string.
            limit: Maximum number of results (default: 25, max: 100).
            offset: Offset for pagination (default: 0).

        Returns:
            Search results containing release groups and metadata.
        """
        if not query.strip():
            raise MusicBrainzValidationError("Query cannot be empty")

        if limit < 1 or limit > 100:
            raise MusicBrainzValidationError("Limit must be between 1 and 100")

        if offset < 0:
            raise MusicBrainzValidationError("Offset must be non-negative")

        params = {
            "query": query,
            "limit": limit,
            "offset": offset,
        }

        return await self._make_request("release-group", params)

    async def lookup_artist(
        self,
        mbid: str,
        inc: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Look up an artist by MBID.

        Args:
            mbid: MusicBrainz ID of the artist.
            inc: List of additional data to include (e.g., ["releases", "recordings"]).

        Returns:
            Artist data.
        """
        self._validate_mbid(mbid)

        params = {}
        if inc:
            params["inc"] = "+".join(inc)

        return await self._make_request(f"artist/{mbid}", params)

    async def lookup_release(
        self,
        mbid: str,
        inc: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Look up a release by MBID.

        Args:
            mbid: MusicBrainz ID of the release.
            inc: List of additional data to include (e.g., ["recordings", "artist-credits"]).

        Returns:
            Release data.
        """
        self._validate_mbid(mbid)

        params = {}
        if inc:
            params["inc"] = "+".join(inc)

        return await self._make_request(f"release/{mbid}", params)

    async def lookup_recording(
        self,
        mbid: str,
        inc: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Look up a recording by MBID.

        Args:
            mbid: MusicBrainz ID of the recording.
            inc: List of additional data to include (e.g., ["releases", "artist-credits"]).

        Returns:
            Recording data.
        """
        self._validate_mbid(mbid)

        params = {}
        if inc:
            params["inc"] = "+".join(inc)

        return await self._make_request(f"recording/{mbid}", params)

    async def lookup_release_group(
        self,
        mbid: str,
        inc: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Look up a release group by MBID.

        Args:
            mbid: MusicBrainz ID of the release group.
            inc: List of additional data to include (e.g., ["releases", "artist-credits"]).

        Returns:
            Release group data.
        """
        self._validate_mbid(mbid)

        params = {}
        if inc:
            params["inc"] = "+".join(inc)

        return await self._make_request(f"release-group/{mbid}", params)

    async def browse_artist_releases(
        self,
        artist_mbid: str,
        limit: int = 25,
        offset: int = 0,
        release_type: Optional[List[str]] = None,
        release_status: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Browse releases by a specific artist.

        Args:
            artist_mbid: MusicBrainz ID of the artist.
            limit: Maximum number of results (default: 25, max: 100).
            offset: Offset for pagination (default: 0).
            release_type: Filter by release type (e.g., ["album", "single"]).
            release_status: Filter by release status (e.g., ["official"]).

        Returns:
            Browse results containing releases and metadata.
        """
        self._validate_mbid(artist_mbid)

        if limit < 1 or limit > 100:
            raise MusicBrainzValidationError("Limit must be between 1 and 100")

        if offset < 0:
            raise MusicBrainzValidationError("Offset must be non-negative")

        params = {
            "artist": artist_mbid,
            "limit": limit,
            "offset": offset,
        }

        if release_type:
            params["type"] = "|".join(release_type)

        if release_status:
            params["status"] = "|".join(release_status)

        return await self._make_request("release", params)

    async def browse_artist_recordings(
        self,
        artist_mbid: str,
        limit: int = 25,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Browse recordings by a specific artist.

        Args:
            artist_mbid: MusicBrainz ID of the artist.
            limit: Maximum number of results (default: 25, max: 100).
            offset: Offset for pagination (default: 0).

        Returns:
            Browse results containing recordings and metadata.
        """
        self._validate_mbid(artist_mbid)

        if limit < 1 or limit > 100:
            raise MusicBrainzValidationError("Limit must be between 1 and 100")

        if offset < 0:
            raise MusicBrainzValidationError("Offset must be non-negative")

        params = {
            "artist": artist_mbid,
            "limit": limit,
            "offset": offset,
        }

        return await self._make_request("recording", params)

    async def lookup_by_mbid(
        self,
        entity_type: str,
        mbid: str,
        inc: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generic lookup method for any entity type by MBID.

        Args:
            entity_type: Type of entity ("artist", "release", "recording", etc.).
            mbid: MusicBrainz ID of the entity.
            inc: List of additional data to include.

        Returns:
            Entity data.
        """
        valid_types = {
            "artist", "release", "recording", "release-group",
            "label", "work", "area", "place", "event", "instrument", "series", "url"
        }

        if entity_type not in valid_types:
            raise MusicBrainzValidationError(
                f"Invalid entity type: {entity_type}. "
                f"Valid types: {', '.join(sorted(valid_types))}"
            )

        self._validate_mbid(mbid)

        params = {}
        if inc:
            params["inc"] = "+".join(inc)

        return await self._make_request(f"{entity_type}/{mbid}", params)
