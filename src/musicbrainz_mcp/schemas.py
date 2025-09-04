"""
Additional schema definitions and validation helpers for MusicBrainz data.

This module provides utility functions and additional schemas for validating
and processing MusicBrainz API responses, including response parsers and
validation helpers.
"""

import re
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel, ValidationError

from .models import (
    Artist,
    BrowseResult,
    Label,
    Recording,
    Release,
    ReleaseGroup,
    SearchResult,
    Work,
)

T = TypeVar('T', bound=BaseModel)


class ResponseParser:
    """Parser for MusicBrainz API responses."""
    
    @staticmethod
    def parse_search_response(
        response_data: Dict[str, Any],
        entity_type: str
    ) -> SearchResult:
        """
        Parse a search response into a SearchResult model.
        
        Args:
            response_data: Raw API response data
            entity_type: Type of entity being searched
            
        Returns:
            Parsed SearchResult object
        """
        # Extract pagination info
        count = response_data.get(f"{entity_type}-count", 0)
        offset = response_data.get(f"{entity_type}-offset", 0)
        
        # Create base result
        result_data = {
            "count": count,
            "offset": offset,
        }
        
        # Add entity-specific results
        entities_key = f"{entity_type}s" if entity_type != "release-group" else "release-groups"
        entities = response_data.get(entities_key, [])
        
        if entities:
            result_data[entities_key.replace("-", "_")] = entities
        
        return SearchResult(**result_data)
    
    @staticmethod
    def parse_browse_response(
        response_data: Dict[str, Any],
        entity_type: str
    ) -> BrowseResult:
        """
        Parse a browse response into a BrowseResult model.
        
        Args:
            response_data: Raw API response data
            entity_type: Type of entity being browsed
            
        Returns:
            Parsed BrowseResult object
        """
        # Extract pagination info
        count = response_data.get(f"{entity_type}-count", 0)
        offset = response_data.get(f"{entity_type}-offset", 0)
        
        # Create base result
        result_data = {
            "count": count,
            "offset": offset,
        }
        
        # Add entity-specific results
        entities_key = f"{entity_type}s" if entity_type != "release-group" else "release-groups"
        entities = response_data.get(entities_key, [])
        
        if entities:
            result_data[entities_key.replace("-", "_")] = entities
        
        return BrowseResult(**result_data)
    
    @staticmethod
    def parse_entity_response(
        response_data: Dict[str, Any],
        entity_type: str
    ) -> Union[Artist, Release, Recording, ReleaseGroup, Label, Work]:
        """
        Parse a single entity response.
        
        Args:
            response_data: Raw API response data
            entity_type: Type of entity
            
        Returns:
            Parsed entity object
        """
        entity_classes = {
            "artist": Artist,
            "release": Release,
            "recording": Recording,
            "release-group": ReleaseGroup,
            "label": Label,
            "work": Work,
        }
        
        entity_class = entity_classes.get(entity_type)
        if not entity_class:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        return entity_class(**response_data)


class ValidationHelpers:
    """Validation helper functions."""
    
    @staticmethod
    def validate_mbid(mbid: str) -> bool:
        """
        Validate that a string is a valid MBID (UUID format).
        
        Args:
            mbid: String to validate
            
        Returns:
            True if valid, False otherwise
        """
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(mbid))
    
    @staticmethod
    def validate_date_string(date_str: str) -> bool:
        """
        Validate MusicBrainz date format (YYYY, YYYY-MM, or YYYY-MM-DD).
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not date_str:
            return True  # Empty dates are allowed
        
        # Match YYYY, YYYY-MM, or YYYY-MM-DD
        date_patterns = [
            r"^\d{4}$",                    # YYYY
            r"^\d{4}-\d{2}$",              # YYYY-MM
            r"^\d{4}-\d{2}-\d{2}$",        # YYYY-MM-DD
        ]
        
        return any(re.match(pattern, date_str) for pattern in date_patterns)
    
    @staticmethod
    def validate_country_code(code: str) -> bool:
        """
        Validate ISO country code format.
        
        Args:
            code: Country code to validate
            
        Returns:
            True if valid format, False otherwise
        """
        if not code:
            return True  # Empty codes are allowed
        
        # ISO 3166-1 alpha-2 codes are 2 uppercase letters
        # Special codes like XW (Worldwide) are also allowed
        return bool(re.match(r"^[A-Z]{2}$", code))
    
    @staticmethod
    def validate_language_code(code: str) -> bool:
        """
        Validate ISO language code format.
        
        Args:
            code: Language code to validate
            
        Returns:
            True if valid format, False otherwise
        """
        if not code:
            return True  # Empty codes are allowed
        
        # ISO 639 codes are typically 2-3 lowercase letters
        # Special codes like 'zxx' (no linguistic content) are also allowed
        return bool(re.match(r"^[a-z]{2,3}$", code))
    
    @staticmethod
    def safe_parse_model(
        model_class: Type[T],
        data: Dict[str, Any],
        default: Optional[T] = None
    ) -> Optional[T]:
        """
        Safely parse data into a Pydantic model.
        
        Args:
            model_class: Pydantic model class
            data: Data to parse
            default: Default value if parsing fails
            
        Returns:
            Parsed model instance or default value
        """
        try:
            return model_class(**data)
        except (ValidationError, TypeError, ValueError):
            return default
    
    @staticmethod
    def clean_api_response(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean API response data by removing null values and normalizing fields.
        
        Args:
            data: Raw API response data
            
        Returns:
            Cleaned data dictionary
        """
        if not isinstance(data, dict):
            return data
        
        cleaned = {}
        for key, value in data.items():
            # Skip null values
            if value is None:
                continue
            
            # Recursively clean nested dictionaries
            if isinstance(value, dict):
                cleaned_value = ValidationHelpers.clean_api_response(value)
                if cleaned_value:  # Only add if not empty
                    cleaned[key] = cleaned_value
            
            # Clean lists
            elif isinstance(value, list):
                cleaned_list = []
                for item in value:
                    if isinstance(item, dict):
                        cleaned_item = ValidationHelpers.clean_api_response(item)
                        if cleaned_item:
                            cleaned_list.append(cleaned_item)
                    elif item is not None:
                        cleaned_list.append(item)
                
                if cleaned_list:  # Only add if not empty
                    cleaned[key] = cleaned_list
            
            # Add non-null primitive values
            else:
                cleaned[key] = value
        
        return cleaned


class EntityTypeMapper:
    """Maps entity types to their corresponding model classes and API endpoints."""
    
    ENTITY_CLASSES = {
        "artist": Artist,
        "release": Release,
        "recording": Recording,
        "release-group": ReleaseGroup,
        "label": Label,
        "work": Work,
    }
    
    API_ENDPOINTS = {
        "artist": "artist",
        "release": "release",
        "recording": "recording",
        "release-group": "release-group",
        "label": "label",
        "work": "work",
    }
    
    @classmethod
    def get_model_class(cls, entity_type: str) -> Optional[Type[BaseModel]]:
        """Get the model class for an entity type."""
        return cls.ENTITY_CLASSES.get(entity_type)
    
    @classmethod
    def get_api_endpoint(cls, entity_type: str) -> Optional[str]:
        """Get the API endpoint for an entity type."""
        return cls.API_ENDPOINTS.get(entity_type)
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported entity types."""
        return list(cls.ENTITY_CLASSES.keys())
