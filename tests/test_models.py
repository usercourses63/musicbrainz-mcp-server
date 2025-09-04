"""
Unit tests for Pydantic data models.

Tests the data models for proper validation, serialization, and handling
of various input scenarios including edge cases and error conditions.
"""

import pytest
from pydantic import ValidationError
from musicbrainz_mcp.models import (
    Artist, Release, Recording, ReleaseGroup, Label, Work,
    LifeSpan, Area, Alias, ArtistCredit, Medium, Track,
    SearchResult, BrowseResult
)
from tests.mock_data import (
    MOCK_ARTIST_BEATLES, MOCK_RELEASE_ABBEY_ROAD,
    MOCK_RECORDING_COME_TOGETHER, MOCK_RELEASE_GROUP_ABBEY_ROAD
)


@pytest.mark.unit
class TestMBIDValidation:
    """Test MBID validation in models."""

    def test_valid_mbid(self):
        """Test that valid MBIDs are accepted."""
        valid_mbid = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
        artist = Artist(id=valid_mbid, name="Test Artist")
        assert artist.id == valid_mbid

    def test_invalid_mbid_format(self):
        """Test that invalid MBID formats are rejected."""
        invalid_mbids = [
            "invalid-mbid",
            "b10bbbfc-cf9e-42e0-be17",  # Too short
            "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d-extra",  # Too long
            "g10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",  # Invalid character
            "",  # Empty
            "B10BBBFC-CF9E-42E0-BE17-E2C3E1D2600D"  # Should work (case insensitive)
        ]
        
        # Most should fail
        for mbid in invalid_mbids[:-1]:  # Exclude the last one (uppercase)
            with pytest.raises(ValidationError):
                Artist(id=mbid, name="Test Artist")
        
        # Uppercase should work (case insensitive)
        artist = Artist(id=invalid_mbids[-1], name="Test Artist")
        assert artist.id == invalid_mbids[-1]


@pytest.mark.unit
class TestArtistModel:
    """Test Artist model validation and serialization."""

    def test_artist_from_mock_data(self):
        """Test creating Artist from mock API data."""
        artist = Artist(**MOCK_ARTIST_BEATLES)
        
        assert artist.id == "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
        assert artist.name == "The Beatles"
        assert artist.sort_name == "Beatles, The"
        assert artist.type == "Group"
        assert artist.country == "GB"
        
        # Test life span
        assert artist.life_span is not None
        assert artist.life_span.begin == "1960"
        assert artist.life_span.end == "1970"
        assert artist.life_span.ended is True

    def test_artist_minimal_data(self):
        """Test Artist with minimal required data."""
        artist = Artist(
            id="b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
            name="Test Artist"
        )
        
        assert artist.id == "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
        assert artist.name == "Test Artist"
        assert artist.sort_name is None
        assert artist.disambiguation == ""
        assert artist.type is None

    def test_artist_serialization(self):
        """Test Artist model serialization."""
        artist = Artist(**MOCK_ARTIST_BEATLES)
        data = artist.model_dump()
        
        assert isinstance(data, dict)
        assert data["id"] == "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
        assert data["name"] == "The Beatles"
        assert "life_span" in data

    def test_artist_with_extra_fields(self):
        """Test that Artist handles extra fields gracefully."""
        data = MOCK_ARTIST_BEATLES.copy()
        data["unknown_field"] = "unknown_value"
        data["score"] = 100  # Common in search results
        
        # Should not raise error due to extra='ignore'
        artist = Artist(**data)
        assert artist.name == "The Beatles"


@pytest.mark.unit
class TestReleaseModel:
    """Test Release model validation and serialization."""

    def test_release_from_mock_data(self):
        """Test creating Release from mock API data."""
        release = Release(**MOCK_RELEASE_ABBEY_ROAD)
        
        assert release.id == "f4a261d1-2a31-4d1a-b4b6-7d6e4c8f9a0b"
        assert release.title == "Abbey Road"
        assert release.date == "1969-09-26"
        assert release.country == "GB"
        assert release.status == "Official"

    def test_release_with_media(self):
        """Test Release with media information."""
        release = Release(**MOCK_RELEASE_ABBEY_ROAD)
        
        assert release.media is not None
        assert len(release.media) == 1
        
        medium = release.media[0]
        assert medium.position == 1
        assert medium.format == "CD"
        assert medium.track_count == 17

    def test_release_artist_credits(self):
        """Test Release with artist credits."""
        release = Release(**MOCK_RELEASE_ABBEY_ROAD)
        
        assert release.artist_credit is not None
        assert len(release.artist_credit) == 1
        
        credit = release.artist_credit[0]
        assert credit.name == "The Beatles"
        assert credit.artist.id == "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"


@pytest.mark.unit
class TestRecordingModel:
    """Test Recording model validation and serialization."""

    def test_recording_from_mock_data(self):
        """Test creating Recording from mock API data."""
        recording = Recording(**MOCK_RECORDING_COME_TOGETHER)
        
        assert recording.id == "c1a2b3d4-e5f6-7890-abcd-ef1234567890"
        assert recording.title == "Come Together"
        assert recording.length == 259000
        assert recording.video is False

    def test_recording_with_isrcs(self):
        """Test Recording with ISRC codes."""
        recording = Recording(**MOCK_RECORDING_COME_TOGETHER)
        
        assert recording.isrcs is not None
        assert len(recording.isrcs) == 1
        assert recording.isrcs[0] == "GBUM71505078"

    def test_recording_optional_fields(self):
        """Test Recording with optional fields as None."""
        recording = Recording(
            id="c1a2b3d4-e5f6-7890-abcd-ef1234567890",
            title="Test Recording"
        )
        
        assert recording.length is None
        assert recording.video is None
        assert recording.artist_credit is None


@pytest.mark.unit
class TestLifeSpanModel:
    """Test LifeSpan model validation."""

    def test_lifespan_complete(self):
        """Test LifeSpan with complete data."""
        lifespan = LifeSpan(begin="1960", end="1970", ended=True)
        
        assert lifespan.begin == "1960"
        assert lifespan.end == "1970"
        assert lifespan.ended is True

    def test_lifespan_ongoing(self):
        """Test LifeSpan for ongoing entity."""
        lifespan = LifeSpan(begin="1941-05-24", ended=False)
        
        assert lifespan.begin == "1941-05-24"
        assert lifespan.end is None
        assert lifespan.ended is False

    def test_lifespan_optional_ended(self):
        """Test LifeSpan with ended as None."""
        lifespan = LifeSpan(begin="1960")
        
        assert lifespan.begin == "1960"
        assert lifespan.end is None
        assert lifespan.ended is None


@pytest.mark.unit
class TestSearchResultModel:
    """Test SearchResult model validation."""

    def test_search_result_artists(self):
        """Test SearchResult with artist data."""
        artists = [Artist(**MOCK_ARTIST_BEATLES)]
        search_result = SearchResult(
            count=1,
            offset=0,
            artists=artists
        )
        
        assert search_result.count == 1
        assert search_result.offset == 0
        assert len(search_result.artists) == 1
        assert search_result.artists[0].name == "The Beatles"

    def test_search_result_empty(self):
        """Test SearchResult with no results."""
        search_result = SearchResult(count=0, offset=0)
        
        assert search_result.count == 0
        assert search_result.artists is None
        assert search_result.releases is None

    def test_search_result_mixed_entities(self):
        """Test SearchResult with multiple entity types."""
        artists = [Artist(**MOCK_ARTIST_BEATLES)]
        releases = [Release(**MOCK_RELEASE_ABBEY_ROAD)]
        
        search_result = SearchResult(
            count=2,
            offset=0,
            artists=artists,
            releases=releases
        )
        
        assert search_result.count == 2
        assert len(search_result.artists) == 1
        assert len(search_result.releases) == 1


@pytest.mark.unit
class TestModelSerialization:
    """Test model serialization and deserialization."""

    def test_artist_round_trip(self):
        """Test Artist serialization and deserialization."""
        original = Artist(**MOCK_ARTIST_BEATLES)

        # Use model_dump with by_alias=True to preserve field names
        data = original.model_dump(by_alias=True)
        restored = Artist(**data)

        assert original.id == restored.id
        assert original.name == restored.name

        # The life_span should be preserved with proper serialization
        if original.life_span is not None:
            assert restored.life_span is not None
            assert original.life_span.begin == restored.life_span.begin

    def test_release_round_trip(self):
        """Test Release serialization and deserialization."""
        original = Release(**MOCK_RELEASE_ABBEY_ROAD)
        data = original.model_dump()
        restored = Release(**data)
        
        assert original.id == restored.id
        assert original.title == restored.title
        assert original.date == restored.date

    def test_model_json_serialization(self):
        """Test JSON serialization of models."""
        artist = Artist(**MOCK_ARTIST_BEATLES)
        json_str = artist.model_dump_json()
        
        assert isinstance(json_str, str)
        assert "The Beatles" in json_str
        assert "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d" in json_str


@pytest.mark.unit
class TestModelValidation:
    """Test model validation edge cases."""

    def test_empty_string_handling(self):
        """Test handling of empty strings."""
        artist = Artist(
            id="b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
            name="Test Artist",
            disambiguation="",  # Empty string should be allowed
            sort_name=""        # Empty string may be converted to None
        )

        assert artist.disambiguation == ""
        # sort_name empty string may be converted to None by Pydantic
        assert artist.sort_name == "" or artist.sort_name is None

    def test_none_vs_empty_list(self):
        """Test distinction between None and empty list."""
        # Test with None
        artist1 = Artist(
            id="b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
            name="Test Artist",
            aliases=None
        )
        assert artist1.aliases is None
        
        # Test with empty list
        artist2 = Artist(
            id="b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
            name="Test Artist",
            aliases=[]
        )
        assert artist2.aliases == []

    def test_field_aliases(self):
        """Test that field aliases work correctly."""
        # Test data with API field names (with hyphens)
        data = {
            "id": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
            "name": "Test Artist",
            "sort-name": "Artist, Test",  # API field name
            "type-id": "test-type-id",    # API field name
            "life-span": {                # API field name
                "begin": "1960",
                "end": "1970",
                "ended": True
            }
        }
        
        artist = Artist(**data)
        assert artist.sort_name == "Artist, Test"
        assert artist.type_id == "test-type-id"
        assert artist.life_span.begin == "1960"
