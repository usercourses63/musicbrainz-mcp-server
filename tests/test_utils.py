"""
Unit tests for utility functions and configuration management.

Tests all utility classes and functions including MBID validation,
caching, response formatting, and configuration management.
"""

import pytest
import time
import tempfile
import json
import os
from datetime import datetime, timezone
from musicbrainz_mcp.utils import (
    MBIDUtils, ResponseFormatter, QueryUtils, CacheUtils,
    PaginationUtils, URLUtils, LoggingUtils, DataUtils, get_cache
)
from musicbrainz_mcp.config import (
    MusicBrainzMCPConfig, APIConfig, CacheConfig, LoggingConfig, ServerConfig,
    get_config, set_config, load_config_from_file
)


@pytest.mark.unit
class TestMBIDUtils:
    """Test MBID utility functions."""

    def test_validate_mbid_valid(self):
        """Test validation of valid MBIDs."""
        valid_mbids = [
            "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
            "B10BBBFC-CF9E-42E0-BE17-E2C3E1D2600D",  # Uppercase
            "72c536dc-7137-4477-a521-567eeb840fa8",
            "00000000-0000-0000-0000-000000000000",  # All zeros
            "ffffffff-ffff-ffff-ffff-ffffffffffff",  # All f's
        ]
        
        for mbid in valid_mbids:
            assert MBIDUtils.validate_mbid(mbid), f"Should validate {mbid}"

    def test_validate_mbid_invalid(self):
        """Test validation of invalid MBIDs."""
        invalid_mbids = [
            "invalid-mbid",
            "b10bbbfc-cf9e-42e0-be17",  # Too short
            "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d-extra",  # Too long
            "g10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",  # Invalid character
            "",  # Empty
            None,  # None
            123,  # Not a string
            "b10bbbfc_cf9e_42e0_be17_e2c3e1d2600d",  # Underscores instead of hyphens
        ]
        
        for mbid in invalid_mbids:
            assert not MBIDUtils.validate_mbid(mbid), f"Should not validate {mbid}"

    def test_normalize_mbid(self):
        """Test MBID normalization."""
        uppercase_mbid = "B10BBBFC-CF9E-42E0-BE17-E2C3E1D2600D"
        expected = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
        
        result = MBIDUtils.normalize_mbid(uppercase_mbid)
        assert result == expected

    def test_normalize_mbid_invalid(self):
        """Test normalization with invalid MBID."""
        with pytest.raises(ValueError):
            MBIDUtils.normalize_mbid("invalid-mbid")

    def test_extract_mbids_from_text(self):
        """Test extracting MBIDs from text."""
        text = """
        Artist MBID: b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d
        Release: F4A261D1-2A31-4D1A-B4B6-7D6E4C8F9A0B
        Invalid: invalid-mbid-format
        Another: 72c536dc-7137-4477-a521-567eeb840fa8
        """
        
        mbids = MBIDUtils.extract_mbids_from_text(text)
        
        assert len(mbids) == 3
        assert "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d" in mbids
        assert "f4a261d1-2a31-4d1a-b4b6-7d6e4c8f9a0b" in mbids  # Normalized to lowercase
        assert "72c536dc-7137-4477-a521-567eeb840fa8" in mbids


@pytest.mark.unit
class TestResponseFormatter:
    """Test response formatting utilities."""

    def test_format_success_response(self):
        """Test formatting success responses."""
        data = {"test": "data"}
        message = "Operation successful"
        metadata = {"count": 1}
        
        response = ResponseFormatter.format_success_response(data, message, metadata)
        
        assert response["success"] is True
        assert response["data"] == data
        assert response["message"] == message
        assert response["metadata"] == metadata
        assert "timestamp" in response
        
        # Verify timestamp format
        timestamp = response["timestamp"]
        assert timestamp.endswith("Z")
        assert "T" in timestamp

    def test_format_error_response(self):
        """Test formatting error responses."""
        error = "Something went wrong"
        error_code = "TEST_ERROR"
        details = {"field": "value"}
        
        response = ResponseFormatter.format_error_response(error, error_code, details)
        
        assert response["success"] is False
        assert response["error"] == error
        assert response["error_code"] == error_code
        assert response["details"] == details
        assert "timestamp" in response

    def test_format_pagination_metadata(self):
        """Test formatting pagination metadata."""
        # Test with total known
        metadata = ResponseFormatter.format_pagination_metadata(25, 0, 25, 100)
        
        assert metadata["count"] == 25
        assert metadata["offset"] == 0
        assert metadata["limit"] == 25
        assert metadata["total"] == 100
        assert metadata["has_more"] is True
        assert metadata["page"] == 1
        assert metadata["total_pages"] == 4
        
        # Test without total
        metadata = ResponseFormatter.format_pagination_metadata(25, 0, 25)
        assert metadata["has_more"] is True  # Assumes more if full page
        assert "total" not in metadata


@pytest.mark.unit
class TestQueryUtils:
    """Test query utility functions."""

    def test_clean_query(self):
        """Test query cleaning."""
        test_cases = [
            ("  The Beatles  ", "The Beatles"),
            ("test   query", "test query"),
            ("", ""),
            ("   ", ""),
            ("a" * 1001, "a" * 1000),  # Length limit
        ]
        
        for input_query, expected in test_cases:
            result = QueryUtils.clean_query(input_query)
            assert result == expected

    def test_escape_lucene_query(self):
        """Test Lucene query escaping."""
        test_cases = [
            ("simple query", "simple query"),
            ("artist:The Beatles", "artist\\:The Beatles"),
            ("test+query", "test\\+query"),
            ("query-with-dash", "query\\-with\\-dash"),
            ("query*with*wildcards", "query\\*with\\*wildcards"),
        ]
        
        for input_query, expected in test_cases:
            result = QueryUtils.escape_lucene_query(input_query)
            assert result == expected

    def test_build_search_query(self):
        """Test building structured search queries."""
        terms = {"artist": "The Beatles", "type": "Group"}
        
        query = QueryUtils.build_search_query(terms, "AND")
        assert "artist:" in query
        assert "type:" in query
        assert " AND " in query
        
        # Test with OR operator
        query = QueryUtils.build_search_query(terms, "OR")
        assert " OR " in query
        
        # Test with empty terms
        query = QueryUtils.build_search_query({})
        assert query == ""


@pytest.mark.unit
class TestCacheUtils:
    """Test caching utilities."""

    def test_cache_basic_operations(self):
        """Test basic cache operations."""
        cache = CacheUtils(default_ttl=60)
        
        # Test set and get
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        
        # Test non-existent key
        assert cache.get("non_existent") is None
        
        # Test delete
        assert cache.delete("test_key") is True
        assert cache.get("test_key") is None
        assert cache.delete("non_existent") is False

    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        cache = CacheUtils(default_ttl=0.1)  # 100ms TTL
        
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        
        # Wait for expiration
        time.sleep(0.2)
        assert cache.get("test_key") is None

    def test_cache_custom_ttl(self):
        """Test cache with custom TTL."""
        cache = CacheUtils(default_ttl=60)
        
        cache.set("test_key", "test_value", ttl=0.1)
        assert cache.get("test_key") == "test_value"
        
        time.sleep(0.2)
        assert cache.get("test_key") is None

    def test_cache_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = CacheUtils(default_ttl=0.1)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        time.sleep(0.2)
        
        # Add a non-expired entry
        cache.set("key3", "value3", ttl=60)
        
        # Cleanup expired entries
        removed_count = cache.cleanup_expired()
        assert removed_count == 2
        assert cache.get("key3") == "value3"

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = CacheUtils(default_ttl=60)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        stats = cache.stats()
        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 2
        assert stats["expired_entries"] == 0
        assert stats["memory_usage_bytes"] > 0

    def test_global_cache(self):
        """Test global cache instance."""
        cache1 = get_cache()
        cache2 = get_cache()
        
        # Should be the same instance
        assert cache1 is cache2
        
        # Test functionality
        cache1.set("global_test", "global_value")
        assert cache2.get("global_test") == "global_value"


@pytest.mark.unit
class TestPaginationUtils:
    """Test pagination utilities."""

    def test_validate_pagination_params_valid(self):
        """Test validation of valid pagination parameters."""
        limit, offset = PaginationUtils.validate_pagination_params(25, 0, 100)
        assert limit == 25
        assert offset == 0

    def test_validate_pagination_params_invalid(self):
        """Test validation of invalid pagination parameters."""
        # Invalid limit
        with pytest.raises(ValueError):
            PaginationUtils.validate_pagination_params(0, 0, 100)
        
        with pytest.raises(ValueError):
            PaginationUtils.validate_pagination_params(101, 0, 100)
        
        # Invalid offset
        with pytest.raises(ValueError):
            PaginationUtils.validate_pagination_params(25, -1, 100)

    def test_calculate_pagination_info(self):
        """Test pagination info calculation."""
        info = PaginationUtils.calculate_pagination_info(100, 25, 25)
        
        assert info["current_page"] == 2
        assert info["total_pages"] == 4
        assert info["items_per_page"] == 25
        assert info["total_items"] == 100
        assert info["has_previous"] is True
        assert info["has_next"] is True
        assert info["previous_offset"] == 0
        assert info["next_offset"] == 50


@pytest.mark.unit
class TestURLUtils:
    """Test URL utilities."""

    def test_build_api_url_basic(self):
        """Test basic URL building."""
        url = URLUtils.build_api_url("https://api.example.com", "search")
        assert url == "https://api.example.com/search"

    def test_build_api_url_with_params(self):
        """Test URL building with parameters."""
        params = {"q": "test query", "limit": 10, "offset": 0}
        url = URLUtils.build_api_url("https://api.example.com", "search", params)
        
        assert "https://api.example.com/search" in url
        assert "q=test%20query" in url
        assert "limit=10" in url
        assert "offset=0" in url

    def test_build_api_url_with_list_params(self):
        """Test URL building with list parameters."""
        params = {"inc": ["releases", "recordings"], "limit": 10}
        url = URLUtils.build_api_url("https://api.example.com", "artist", params)
        
        assert "inc=releases%2Brecordings" in url
        assert "limit=10" in url

    def test_extract_query_params(self):
        """Test extracting query parameters from URL."""
        url = "https://api.example.com/search?q=test&limit=10&offset=0"
        params = URLUtils.extract_query_params(url)
        
        assert params["q"] == "test"
        assert params["limit"] == "10"
        assert params["offset"] == "0"


@pytest.mark.unit
class TestDataUtils:
    """Test data utilities."""

    def test_safe_get_simple(self):
        """Test safe get with simple keys."""
        data = {"key1": "value1", "key2": "value2"}
        
        assert DataUtils.safe_get(data, "key1") == "value1"
        assert DataUtils.safe_get(data, "key3", "default") == "default"

    def test_safe_get_dot_notation(self):
        """Test safe get with dot notation."""
        data = {
            "artist": {
                "name": "The Beatles",
                "country": "GB",
                "area": {
                    "name": "United Kingdom"
                }
            }
        }
        
        assert DataUtils.safe_get(data, "artist.name") == "The Beatles"
        assert DataUtils.safe_get(data, "artist.area.name") == "United Kingdom"
        assert DataUtils.safe_get(data, "artist.missing", "default") == "default"

    def test_flatten_dict(self):
        """Test dictionary flattening."""
        data = {
            "artist": {
                "name": "The Beatles",
                "country": "GB"
            },
            "releases": [
                {"title": "Abbey Road"},
                {"title": "Let It Be"}
            ]
        }
        
        flattened = DataUtils.flatten_dict(data)
        
        assert flattened["artist.name"] == "The Beatles"
        assert flattened["artist.country"] == "GB"
        assert flattened["releases[0].title"] == "Abbey Road"
        assert flattened["releases[1].title"] == "Let It Be"

    def test_clean_dict(self):
        """Test dictionary cleaning."""
        data = {
            "key1": "value1",
            "key2": None,
            "key3": "",
            "key4": [],
            "key5": {},
            "key6": "value6"
        }
        
        # Remove None values only
        cleaned = DataUtils.clean_dict(data, remove_none=True, remove_empty=False)
        assert "key1" in cleaned
        assert "key2" not in cleaned
        assert "key3" in cleaned  # Empty string kept
        
        # Remove None and empty values
        cleaned = DataUtils.clean_dict(data, remove_none=True, remove_empty=True)
        assert "key1" in cleaned
        assert "key2" not in cleaned
        assert "key3" not in cleaned  # Empty string removed
        assert "key4" not in cleaned  # Empty list removed
        assert "key6" in cleaned
