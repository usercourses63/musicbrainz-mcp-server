"""
Utility Functions and Helpers

This module provides utility functions for common operations like MBID validation,
response formatting, caching helpers, and other reusable functionality to support
the main server functionality.
"""

import hashlib
import json
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union, Tuple
from urllib.parse import quote, unquote

# Configure module logger
logger = logging.getLogger(__name__)


class MBIDUtils:
    """Utilities for working with MusicBrainz IDs."""
    
    @staticmethod
    def validate_mbid(mbid: str) -> bool:
        """
        Validate that a string is a valid MBID (UUID format).
        
        Args:
            mbid: String to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not mbid or not isinstance(mbid, str):
            return False
        
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(mbid.strip()))
    
    @staticmethod
    def normalize_mbid(mbid: str) -> str:
        """
        Normalize an MBID to lowercase format.
        
        Args:
            mbid: MBID to normalize
            
        Returns:
            Normalized MBID
            
        Raises:
            ValueError: If MBID is invalid
        """
        if not MBIDUtils.validate_mbid(mbid):
            raise ValueError(f"Invalid MBID format: {mbid}")
        
        return mbid.strip().lower()
    
    @staticmethod
    def extract_mbids_from_text(text: str) -> List[str]:
        """
        Extract all valid MBIDs from a text string.
        
        Args:
            text: Text to search for MBIDs
            
        Returns:
            List of valid MBIDs found
        """
        uuid_pattern = re.compile(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
            re.IGNORECASE
        )
        
        matches = uuid_pattern.findall(text)
        return [match.lower() for match in matches]


class ResponseFormatter:
    """Utilities for formatting API responses consistently."""
    
    @staticmethod
    def format_success_response(
        data: Any,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format a successful response.
        
        Args:
            data: Response data
            message: Optional success message
            metadata: Optional metadata
            
        Returns:
            Formatted response dictionary
        """
        response = {
            "success": True,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
        
        if message:
            response["message"] = message
        
        if metadata:
            response["metadata"] = metadata
        
        return response
    
    @staticmethod
    def format_error_response(
        error: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format an error response.
        
        Args:
            error: Error message
            error_code: Optional error code
            details: Optional error details
            
        Returns:
            Formatted error response dictionary
        """
        response = {
            "success": False,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
        
        if error_code:
            response["error_code"] = error_code
        
        if details:
            response["details"] = details
        
        return response
    
    @staticmethod
    def format_pagination_metadata(
        count: int,
        offset: int,
        limit: int,
        total: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Format pagination metadata.
        
        Args:
            count: Number of items in current page
            offset: Current offset
            limit: Items per page
            total: Total number of items (if known)
            
        Returns:
            Pagination metadata dictionary
        """
        metadata = {
            "count": count,
            "offset": offset,
            "limit": limit,
            "has_more": count == limit  # Assume more if we got a full page
        }
        
        if total is not None:
            metadata["total"] = total
            metadata["has_more"] = (offset + count) < total
            metadata["page"] = (offset // limit) + 1
            metadata["total_pages"] = (total + limit - 1) // limit
        
        return metadata


class QueryUtils:
    """Utilities for working with search queries and parameters."""
    
    @staticmethod
    def clean_query(query: str) -> str:
        """
        Clean and normalize a search query.
        
        Args:
            query: Raw search query
            
        Returns:
            Cleaned query string
        """
        if not query:
            return ""
        
        # Strip whitespace and normalize
        cleaned = query.strip()
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Basic length validation
        if len(cleaned) > 1000:
            cleaned = cleaned[:1000]
        
        return cleaned
    
    @staticmethod
    def escape_lucene_query(query: str) -> str:
        """
        Escape special characters in Lucene queries.
        
        Args:
            query: Query to escape
            
        Returns:
            Escaped query string
        """
        # Lucene special characters that need escaping
        special_chars = r'+-&|!(){}[]^"~*?:\\'
        
        escaped = ""
        for char in query:
            if char in special_chars:
                escaped += "\\" + char
            else:
                escaped += char
        
        return escaped
    
    @staticmethod
    def build_search_query(
        terms: Dict[str, str],
        operator: str = "AND"
    ) -> str:
        """
        Build a structured search query from terms.
        
        Args:
            terms: Dictionary of field:value pairs
            operator: Logical operator (AND/OR)
            
        Returns:
            Formatted search query string
        """
        if not terms:
            return ""
        
        query_parts = []
        for field, value in terms.items():
            if value:
                # Escape the value
                escaped_value = QueryUtils.escape_lucene_query(str(value))
                # Add quotes if value contains spaces
                if " " in escaped_value:
                    escaped_value = f'"{escaped_value}"'
                query_parts.append(f"{field}:{escaped_value}")
        
        return f" {operator} ".join(query_parts)


class CacheUtils:
    """Simple in-memory caching utilities."""
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache with default TTL.
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if time.time() > entry["expires_at"]:
            del self._cache[key]
            return None
        
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self._default_ttl
        
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
            "created_at": time.time()
        }
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time > entry["expires_at"]
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)
    
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        current_time = time.time()
        expired_count = sum(
            1 for entry in self._cache.values()
            if current_time > entry["expires_at"]
        )
        
        return {
            "total_entries": len(self._cache),
            "expired_entries": expired_count,
            "active_entries": len(self._cache) - expired_count,
            "memory_usage_bytes": sum(
                len(str(entry)) for entry in self._cache.values()
            )
        }


class PaginationUtils:
    """Utilities for handling pagination."""
    
    @staticmethod
    def validate_pagination_params(
        limit: int,
        offset: int,
        max_limit: int = 100
    ) -> Tuple[int, int]:
        """
        Validate and normalize pagination parameters.
        
        Args:
            limit: Requested limit
            offset: Requested offset
            max_limit: Maximum allowed limit
            
        Returns:
            Tuple of (validated_limit, validated_offset)
            
        Raises:
            ValueError: If parameters are invalid
        """
        if limit < 1:
            raise ValueError("Limit must be at least 1")
        
        if limit > max_limit:
            raise ValueError(f"Limit cannot exceed {max_limit}")
        
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        
        return limit, offset
    
    @staticmethod
    def calculate_pagination_info(
        total_items: int,
        current_offset: int,
        current_limit: int
    ) -> Dict[str, Any]:
        """
        Calculate pagination information.
        
        Args:
            total_items: Total number of items
            current_offset: Current offset
            current_limit: Current limit
            
        Returns:
            Dictionary with pagination information
        """
        current_page = (current_offset // current_limit) + 1
        total_pages = (total_items + current_limit - 1) // current_limit
        
        return {
            "current_page": current_page,
            "total_pages": total_pages,
            "items_per_page": current_limit,
            "total_items": total_items,
            "has_previous": current_offset > 0,
            "has_next": (current_offset + current_limit) < total_items,
            "previous_offset": max(0, current_offset - current_limit) if current_offset > 0 else None,
            "next_offset": current_offset + current_limit if (current_offset + current_limit) < total_items else None
        }


# Global cache instance
_global_cache = CacheUtils(default_ttl=300)  # 5 minutes default TTL


def get_cache() -> CacheUtils:
    """Get the global cache instance."""
    return _global_cache


class URLUtils:
    """Utilities for working with URLs and query parameters."""

    @staticmethod
    def build_api_url(
        base_url: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build a complete API URL with query parameters.

        Args:
            base_url: Base API URL
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Complete URL string
        """
        # Ensure base_url doesn't end with slash and endpoint doesn't start with slash
        base_url = base_url.rstrip('/')
        endpoint = endpoint.lstrip('/')

        url = f"{base_url}/{endpoint}"

        if params:
            query_parts = []
            for key, value in params.items():
                if value is not None:
                    if isinstance(value, list):
                        # Handle list parameters (e.g., inc=releases+recordings)
                        value_str = "+".join(str(v) for v in value)
                    else:
                        value_str = str(value)

                    query_parts.append(f"{quote(str(key))}={quote(value_str)}")

            if query_parts:
                url += "?" + "&".join(query_parts)

        return url

    @staticmethod
    def extract_query_params(url: str) -> Dict[str, str]:
        """
        Extract query parameters from a URL.

        Args:
            url: URL to parse

        Returns:
            Dictionary of query parameters
        """
        from urllib.parse import urlparse, parse_qs

        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        # Convert lists to single values (take first value)
        return {key: values[0] if values else "" for key, values in params.items()}


class LoggingUtils:
    """Utilities for logging configuration and management."""

    @staticmethod
    def setup_logger(
        name: str,
        level: str = "INFO",
        format_string: Optional[str] = None,
        log_file: Optional[str] = None
    ) -> logging.Logger:
        """
        Set up a logger with specified configuration.

        Args:
            name: Logger name
            level: Logging level
            format_string: Log format string
            log_file: Optional log file path

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))

        # Clear existing handlers
        logger.handlers.clear()

        # Create formatter
        if format_string is None:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        formatter = logging.Formatter(format_string)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    @staticmethod
    def log_function_call(
        logger: logging.Logger,
        func_name: str,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        level: str = "DEBUG"
    ) -> None:
        """
        Log a function call with its parameters.

        Args:
            logger: Logger instance
            func_name: Function name
            args: Function arguments
            kwargs: Function keyword arguments
            level: Log level
        """
        if kwargs is None:
            kwargs = {}

        log_level = getattr(logging, level.upper())

        if logger.isEnabledFor(log_level):
            args_str = ", ".join(repr(arg) for arg in args)
            kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())

            params = []
            if args_str:
                params.append(args_str)
            if kwargs_str:
                params.append(kwargs_str)

            params_str = ", ".join(params)
            logger.log(log_level, f"Calling {func_name}({params_str})")


class DataUtils:
    """Utilities for data processing and transformation."""

    @staticmethod
    def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """
        Safely get a value from a dictionary with dot notation support.

        Args:
            data: Dictionary to search
            key: Key to look for (supports dot notation like "artist.name")
            default: Default value if key not found

        Returns:
            Value from dictionary or default
        """
        if not isinstance(data, dict):
            return default

        keys = key.split('.')
        current = data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default

        return current

    @staticmethod
    def flatten_dict(
        data: Dict[str, Any],
        separator: str = ".",
        prefix: str = ""
    ) -> Dict[str, Any]:
        """
        Flatten a nested dictionary.

        Args:
            data: Dictionary to flatten
            separator: Separator for nested keys
            prefix: Prefix for keys

        Returns:
            Flattened dictionary
        """
        result = {}

        for key, value in data.items():
            new_key = f"{prefix}{separator}{key}" if prefix else key

            if isinstance(value, dict):
                result.update(DataUtils.flatten_dict(value, separator, new_key))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        result.update(DataUtils.flatten_dict(item, separator, f"{new_key}[{i}]"))
                    else:
                        result[f"{new_key}[{i}]"] = item
            else:
                result[new_key] = value

        return result

    @staticmethod
    def clean_dict(data: Dict[str, Any], remove_none: bool = True, remove_empty: bool = False) -> Dict[str, Any]:
        """
        Clean a dictionary by removing None/empty values.

        Args:
            data: Dictionary to clean
            remove_none: Remove None values
            remove_empty: Remove empty strings/lists/dicts

        Returns:
            Cleaned dictionary
        """
        cleaned = {}

        for key, value in data.items():
            # Skip None values if requested
            if remove_none and value is None:
                continue

            # Skip empty values if requested
            if remove_empty and value in ("", [], {}):
                continue

            # Recursively clean nested dictionaries
            if isinstance(value, dict):
                cleaned_value = DataUtils.clean_dict(value, remove_none, remove_empty)
                if cleaned_value or not remove_empty:
                    cleaned[key] = cleaned_value
            else:
                cleaned[key] = value

        return cleaned
