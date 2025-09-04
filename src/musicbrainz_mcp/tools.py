"""
MCP Tool Definitions and Helpers

This module provides additional tool definitions, parameter validation,
and helper functions for the MusicBrainz MCP server.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from .schemas import ValidationHelpers


class ToolResponse(BaseModel):
    """Standard response format for MCP tools."""
    
    success: bool = Field(True, description="Whether the operation was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if operation failed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class SearchToolParams(BaseModel):
    """Enhanced search parameters with validation."""
    
    query: str = Field(..., description="Search query string", min_length=1)
    limit: int = Field(25, description="Maximum number of results", ge=1, le=100)
    offset: int = Field(0, description="Offset for pagination", ge=0)
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate that query is not empty or just whitespace."""
        if not v.strip():
            raise ValueError("Query cannot be empty or just whitespace")
        return v.strip()


class LookupToolParams(BaseModel):
    """Enhanced lookup parameters with MBID validation."""
    
    mbid: str = Field(..., description="MusicBrainz ID (UUID format)")
    inc: Optional[List[str]] = Field(None, description="Additional data to include")
    
    @field_validator('mbid')
    @classmethod
    def validate_mbid(cls, v: str) -> str:
        """Validate MBID format."""
        if not ValidationHelpers.validate_mbid(v):
            raise ValueError(f"Invalid MBID format: {v}")
        return v
    
    @field_validator('inc')
    @classmethod
    def validate_inc(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate include parameters."""
        if v is None:
            return v
        
        # Common valid include parameters for different entity types
        valid_includes = {
            'artist': [
                'recordings', 'releases', 'release-groups', 'works',
                'various-artists', 'discids', 'media', 'isrcs', 'artist-rels',
                'label-rels', 'recording-rels', 'release-rels', 'release-group-rels',
                'url-rels', 'work-rels', 'annotation', 'aliases', 'tags', 'ratings'
            ],
            'release': [
                'artists', 'collections', 'labels', 'recordings', 'release-groups',
                'media', 'artist-credits', 'discids', 'puids', 'echoprints', 'isrcs',
                'artist-rels', 'label-rels', 'recording-rels', 'release-rels',
                'release-group-rels', 'url-rels', 'work-rels', 'annotation',
                'aliases', 'tags', 'ratings'
            ],
            'recording': [
                'artists', 'releases', 'puids', 'echoprints', 'isrcs',
                'artist-rels', 'label-rels', 'recording-rels', 'release-rels',
                'release-group-rels', 'url-rels', 'work-rels', 'annotation',
                'aliases', 'tags', 'ratings'
            ]
        }
        
        # For now, just return the list as-is since validation depends on entity type
        # which we don't know at this level
        return v


class BrowseToolParams(BaseModel):
    """Enhanced browse parameters with validation."""
    
    artist_mbid: str = Field(..., description="MusicBrainz ID of the artist")
    limit: int = Field(25, description="Maximum number of results", ge=1, le=100)
    offset: int = Field(0, description="Offset for pagination", ge=0)
    release_type: Optional[List[str]] = Field(None, description="Filter by release type")
    release_status: Optional[List[str]] = Field(None, description="Filter by release status")
    
    @field_validator('artist_mbid')
    @classmethod
    def validate_artist_mbid(cls, v: str) -> str:
        """Validate artist MBID format."""
        if not ValidationHelpers.validate_mbid(v):
            raise ValueError(f"Invalid artist MBID format: {v}")
        return v
    
    @field_validator('release_type')
    @classmethod
    def validate_release_type(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate release type filters."""
        if v is None:
            return v
        
        valid_types = {
            'album', 'single', 'ep', 'compilation', 'soundtrack', 'spokenword',
            'interview', 'audiobook', 'live', 'remix', 'dj-mix', 'mixtape/street',
            'demo', 'broadcast'
        }
        
        for release_type in v:
            if release_type.lower() not in valid_types:
                raise ValueError(f"Invalid release type: {release_type}")
        
        return [rt.lower() for rt in v]
    
    @field_validator('release_status')
    @classmethod
    def validate_release_status(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate release status filters."""
        if v is None:
            return v
        
        valid_statuses = {
            'official', 'promotion', 'bootleg', 'pseudo-release'
        }
        
        for status in v:
            if status.lower() not in valid_statuses:
                raise ValueError(f"Invalid release status: {status}")
        
        return [s.lower() for s in v]


class GenericLookupToolParams(BaseModel):
    """Enhanced generic lookup parameters with validation."""
    
    entity_type: str = Field(..., description="Type of entity")
    mbid: str = Field(..., description="MusicBrainz ID (UUID format)")
    inc: Optional[List[str]] = Field(None, description="Additional data to include")
    
    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        """Validate entity type."""
        valid_types = {
            'artist', 'release', 'recording', 'release-group',
            'label', 'work', 'area', 'place', 'event', 'instrument', 'series', 'url'
        }
        
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid entity type: {v}. Valid types: {', '.join(sorted(valid_types))}")
        
        return v.lower()
    
    @field_validator('mbid')
    @classmethod
    def validate_mbid(cls, v: str) -> str:
        """Validate MBID format."""
        if not ValidationHelpers.validate_mbid(v):
            raise ValueError(f"Invalid MBID format: {v}")
        return v


def format_tool_response(
    success: bool = True,
    data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format a standardized tool response.
    
    Args:
        success: Whether the operation was successful
        data: Response data
        error: Error message if operation failed
        metadata: Additional metadata
        
    Returns:
        Formatted response dictionary
    """
    response = ToolResponse(
        success=success,
        data=data,
        error=error,
        metadata=metadata
    )
    
    return response.model_dump(exclude_none=True)


def validate_search_query(query: str) -> str:
    """
    Validate and clean a search query.
    
    Args:
        query: Raw search query
        
    Returns:
        Cleaned and validated query
        
    Raises:
        ValueError: If query is invalid
    """
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")
    
    cleaned = query.strip()
    
    # Basic length validation
    if len(cleaned) > 1000:
        raise ValueError("Search query is too long (max 1000 characters)")
    
    return cleaned


def validate_pagination_params(limit: int, offset: int) -> tuple[int, int]:
    """
    Validate pagination parameters.
    
    Args:
        limit: Maximum number of results
        offset: Offset for pagination
        
    Returns:
        Validated (limit, offset) tuple
        
    Raises:
        ValueError: If parameters are invalid
    """
    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100")
    
    if offset < 0:
        raise ValueError("Offset must be non-negative")
    
    return limit, offset


def get_entity_type_info(entity_type: str) -> Dict[str, Any]:
    """
    Get information about a specific entity type.
    
    Args:
        entity_type: The entity type
        
    Returns:
        Dictionary with entity type information
    """
    entity_info = {
        'artist': {
            'description': 'Musical artists, bands, orchestras, choirs, etc.',
            'common_includes': ['releases', 'recordings', 'release-groups', 'works'],
            'browse_by': ['area', 'collection', 'recording', 'release', 'release-group', 'work']
        },
        'release': {
            'description': 'Specific release of an album, single, etc.',
            'common_includes': ['artists', 'recordings', 'release-groups', 'media'],
            'browse_by': ['artist', 'collection', 'label', 'recording', 'release-group', 'track', 'track_artist']
        },
        'recording': {
            'description': 'Individual tracks or songs',
            'common_includes': ['artists', 'releases', 'isrcs'],
            'browse_by': ['artist', 'collection', 'release']
        },
        'release-group': {
            'description': 'Groups of related releases',
            'common_includes': ['artists', 'releases'],
            'browse_by': ['artist', 'collection', 'release']
        },
        'label': {
            'description': 'Record labels',
            'common_includes': ['releases'],
            'browse_by': ['area', 'collection', 'release']
        },
        'work': {
            'description': 'Musical compositions',
            'common_includes': ['artists'],
            'browse_by': ['artist', 'collection']
        }
    }
    
    return entity_info.get(entity_type, {
        'description': f'MusicBrainz {entity_type} entity',
        'common_includes': [],
        'browse_by': []
    })
