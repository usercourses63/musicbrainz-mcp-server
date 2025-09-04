"""
Pydantic data models for MusicBrainz entities.

This module defines Pydantic models that correspond to MusicBrainz API response
structures, providing type safety, validation, and serialization for all major
entity types including Artist, Release, Recording, ReleaseGroup, Label, and Work.
"""

import re
from datetime import date
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


class MBIDMixin(BaseModel):
    """Mixin for models that have MusicBrainz IDs."""

    model_config = ConfigDict(extra='ignore')  # Allow extra fields from API

    id: str = Field(..., description="MusicBrainz ID (UUID)")

    @field_validator('id')
    @classmethod
    def validate_mbid(cls, v: str) -> str:
        """Validate that the ID is a valid UUID format."""
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE
        )
        if not uuid_pattern.match(v):
            raise ValueError(f"Invalid MBID format: {v}")
        return v


class LifeSpan(BaseModel):
    """Life span information for entities."""

    model_config = ConfigDict(extra='ignore')  # Allow extra fields from API

    begin: Optional[str] = Field(None, description="Begin date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    end: Optional[str] = Field(None, description="End date (YYYY, YYYY-MM, or YYYY-MM-DD)")
    ended: Optional[bool] = Field(None, description="Whether the entity has ended")


class Coordinates(BaseModel):
    """Geographic coordinates."""

    model_config = ConfigDict(extra='ignore')

    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")


class Area(MBIDMixin):
    """Geographic area (country, city, etc.)."""

    name: str = Field(..., description="Area name")
    sort_name: Optional[str] = Field(None, alias="sort-name", description="Sort name")
    disambiguation: str = Field("", description="Disambiguation comment")
    type: Optional[str] = Field(None, description="Area type")
    type_id: Optional[str] = Field(None, alias="type-id", description="Area type ID")
    iso_3166_1_codes: Optional[List[str]] = Field(None, alias="iso-3166-1-codes", description="ISO 3166-1 codes")
    iso_3166_2_codes: Optional[List[str]] = Field(None, alias="iso-3166-2-codes", description="ISO 3166-2 codes")
    life_span: Optional[LifeSpan] = Field(None, alias="life-span", description="Life span")


class Alias(BaseModel):
    """Alias information for entities."""

    model_config = ConfigDict(extra='ignore')  # Allow extra fields like begin-date, end-date

    name: str = Field(..., description="Alias name")
    sort_name: Optional[str] = Field(None, alias="sort-name", description="Sort name")
    type: Optional[str] = Field(None, description="Alias type")
    type_id: Optional[str] = Field(None, alias="type-id", description="Alias type ID")
    locale: Optional[str] = Field(None, description="Locale")
    primary: Optional[bool] = Field(None, description="Whether this is the primary alias")
    begin: Optional[str] = Field(None, description="Begin date")
    end: Optional[str] = Field(None, description="End date")
    ended: Optional[bool] = Field(None, description="Whether the alias has ended")


class TextRepresentation(BaseModel):
    """Text representation information."""

    model_config = ConfigDict(extra='ignore')

    language: Optional[str] = Field(None, description="Language code")
    script: Optional[str] = Field(None, description="Script code")


class Artist(MBIDMixin):
    """Artist entity."""

    name: str = Field(..., description="Artist name")
    sort_name: Optional[str] = Field(None, alias="sort-name", description="Sort name")
    disambiguation: str = Field("", description="Disambiguation comment")
    type: Optional[str] = Field(None, description="Artist type (Person, Group, etc.)")
    type_id: Optional[str] = Field(None, alias="type-id", description="Artist type ID")
    gender: Optional[str] = Field(None, description="Gender (for persons)")
    gender_id: Optional[str] = Field(None, alias="gender-id", description="Gender ID")
    country: Optional[str] = Field(None, description="Country code")
    area: Optional[Area] = Field(None, description="Main area")
    begin_area: Optional[Area] = Field(None, alias="begin-area", description="Begin area")
    end_area: Optional[Area] = Field(None, alias="end-area", description="End area")
    life_span: Optional[LifeSpan] = Field(None, alias="life-span", description="Life span")
    aliases: Optional[List[Alias]] = Field(None, description="Aliases")
    ipis: Optional[List[str]] = Field(None, description="IPI codes")
    isnis: Optional[List[str]] = Field(None, description="ISNI codes")


class ArtistCredit(BaseModel):
    """Artist credit information."""

    model_config = ConfigDict(extra='ignore')

    name: str = Field(..., description="Credited name")
    joinphrase: str = Field("", description="Join phrase")
    artist: Artist = Field(..., description="Artist information")


class Label(MBIDMixin):
    """Label entity."""

    name: str = Field(..., description="Label name")
    sort_name: Optional[str] = Field(None, alias="sort-name", description="Sort name")
    disambiguation: str = Field("", description="Disambiguation comment")
    type: Optional[str] = Field(None, description="Label type")
    type_id: Optional[str] = Field(None, alias="type-id", description="Label type ID")
    label_code: Optional[int] = Field(None, alias="label-code", description="Label code")
    country: Optional[str] = Field(None, description="Country code")
    area: Optional[Area] = Field(None, description="Area")
    life_span: Optional[LifeSpan] = Field(None, alias="life-span", description="Life span")
    aliases: Optional[List[Alias]] = Field(None, description="Aliases")
    ipis: Optional[List[str]] = Field(None, description="IPI codes")
    isnis: Optional[List[str]] = Field(None, description="ISNI codes")


class LabelInfo(BaseModel):
    """Label information for releases."""

    model_config = ConfigDict(extra='ignore')

    catalog_number: Optional[str] = Field(None, alias="catalog-number", description="Catalog number")
    label: Optional[Label] = Field(None, description="Label information")


class CoverArtArchive(BaseModel):
    """Cover Art Archive information."""

    model_config = ConfigDict(extra='ignore')

    artwork: bool = Field(False, description="Whether artwork is available")
    count: int = Field(0, description="Number of images")
    front: bool = Field(False, description="Whether front cover is available")
    back: bool = Field(False, description="Whether back cover is available")
    darkened: bool = Field(False, description="Whether images are darkened")


class ReleaseEvent(BaseModel):
    """Release event information."""

    model_config = ConfigDict(extra='ignore')

    date: Optional[str] = Field(None, description="Release date")
    area: Optional[Area] = Field(None, description="Release area")


class Recording(MBIDMixin):
    """Recording entity."""

    title: str = Field(..., description="Recording title")
    disambiguation: str = Field("", description="Disambiguation comment")
    length: Optional[int] = Field(None, description="Length in milliseconds")
    video: Optional[bool] = Field(None, description="Whether this is a video recording")
    artist_credit: Optional[List[ArtistCredit]] = Field(None, alias="artist-credit", description="Artist credits")
    isrcs: Optional[List[str]] = Field(None, description="ISRC codes")


class Track(BaseModel):
    """Track information."""

    model_config = ConfigDict(extra='ignore')

    id: Optional[str] = Field(None, description="Track ID")
    title: Optional[str] = Field(None, description="Track title")
    length: Optional[int] = Field(None, description="Length in milliseconds")
    number: Optional[str] = Field(None, description="Track number")
    position: Optional[int] = Field(None, description="Track position")
    artist_credit: Optional[List[ArtistCredit]] = Field(None, alias="artist-credit", description="Artist credits")
    recording: Optional[Recording] = Field(None, description="Recording information")


class Disc(BaseModel):
    """Disc information."""

    model_config = ConfigDict(extra='ignore')

    id: Optional[str] = Field(None, description="Disc ID")
    sectors: Optional[int] = Field(None, description="Number of sectors")
    offsets: Optional[List[int]] = Field(None, description="Track offsets")
    offset_count: Optional[int] = Field(None, alias="offset-count", description="Number of offsets")


class Medium(BaseModel):
    """Medium information (CD, vinyl, etc.)."""

    model_config = ConfigDict(extra='ignore')

    position: Optional[int] = Field(None, description="Medium position")
    title: Optional[str] = Field(None, description="Medium title")
    format: Optional[str] = Field(None, description="Medium format")
    format_id: Optional[str] = Field(None, alias="format-id", description="Medium format ID")
    track_count: Optional[int] = Field(None, alias="track-count", description="Number of tracks")
    track_offset: Optional[int] = Field(None, alias="track-offset", description="Track offset")
    tracks: Optional[List[Track]] = Field(None, description="Track list")
    discs: Optional[List[Disc]] = Field(None, description="Disc list")


class Release(MBIDMixin):
    """Release entity."""

    title: str = Field(..., description="Release title")
    disambiguation: str = Field("", description="Disambiguation comment")
    artist_credit: Optional[List[ArtistCredit]] = Field(None, alias="artist-credit", description="Artist credits")
    date: Optional[str] = Field(None, description="Release date")
    country: Optional[str] = Field(None, description="Country code")
    status: Optional[str] = Field(None, description="Release status")
    status_id: Optional[str] = Field(None, alias="status-id", description="Release status ID")
    packaging: Optional[str] = Field(None, description="Packaging type")
    packaging_id: Optional[str] = Field(None, alias="packaging-id", description="Packaging type ID")
    quality: Optional[str] = Field(None, description="Data quality")
    barcode: Optional[str] = Field(None, description="Barcode")
    asin: Optional[str] = Field(None, description="Amazon ASIN")
    text_representation: Optional[TextRepresentation] = Field(None, alias="text-representation", description="Text representation")
    release_events: Optional[List[ReleaseEvent]] = Field(None, alias="release-events", description="Release events")
    label_info: Optional[List[LabelInfo]] = Field(None, alias="label-info", description="Label information")
    media: Optional[List[Medium]] = Field(None, description="Media list")
    cover_art_archive: Optional[CoverArtArchive] = Field(None, alias="cover-art-archive", description="Cover art archive")


class ReleaseGroup(MBIDMixin):
    """Release group entity."""

    title: str = Field(..., description="Release group title")
    disambiguation: str = Field("", description="Disambiguation comment")
    artist_credit: Optional[List[ArtistCredit]] = Field(None, alias="artist-credit", description="Artist credits")
    first_release_date: Optional[str] = Field(None, alias="first-release-date", description="First release date")
    primary_type: Optional[str] = Field(None, alias="primary-type", description="Primary type")
    primary_type_id: Optional[str] = Field(None, alias="primary-type-id", description="Primary type ID")
    secondary_types: Optional[List[str]] = Field(None, alias="secondary-types", description="Secondary types")
    secondary_type_ids: Optional[List[str]] = Field(None, alias="secondary-type-ids", description="Secondary type IDs")
    releases: Optional[List[Release]] = Field(None, description="Releases in this group")


class Work(MBIDMixin):
    """Work entity."""

    title: str = Field(..., description="Work title")
    disambiguation: str = Field("", description="Disambiguation comment")
    type: Optional[str] = Field(None, description="Work type")
    type_id: Optional[str] = Field(None, alias="type-id", description="Work type ID")
    languages: Optional[List[str]] = Field(None, description="Language codes")
    iswcs: Optional[List[str]] = Field(None, description="ISWC codes")
    attributes: Optional[List[Dict[str, Any]]] = Field(None, description="Work attributes")


class Genre(BaseModel):
    """Genre information."""

    model_config = ConfigDict(extra='ignore')

    id: Optional[str] = Field(None, description="Genre ID")
    name: str = Field(..., description="Genre name")
    disambiguation: str = Field("", description="Disambiguation comment")
    count: Optional[int] = Field(None, description="Usage count")


class Tag(BaseModel):
    """Tag information."""

    model_config = ConfigDict(extra='ignore')

    name: str = Field(..., description="Tag name")
    count: int = Field(0, description="Usage count")


class Rating(BaseModel):
    """Rating information."""

    model_config = ConfigDict(extra='ignore')

    value: Optional[float] = Field(None, description="Rating value")
    votes_count: Optional[int] = Field(None, alias="votes-count", description="Number of votes")


class SearchResult(BaseModel):
    """Generic search result container."""

    model_config = ConfigDict(extra='ignore')

    count: int = Field(0, description="Total number of results")
    offset: int = Field(0, description="Result offset")
    artists: Optional[List[Artist]] = Field(None, description="Artist results")
    releases: Optional[List[Release]] = Field(None, description="Release results")
    recordings: Optional[List[Recording]] = Field(None, description="Recording results")
    release_groups: Optional[List[ReleaseGroup]] = Field(None, alias="release-groups", description="Release group results")
    labels: Optional[List[Label]] = Field(None, description="Label results")
    works: Optional[List[Work]] = Field(None, description="Work results")


class BrowseResult(BaseModel):
    """Generic browse result container."""

    model_config = ConfigDict(extra='ignore')

    count: int = Field(0, description="Total number of results")
    offset: int = Field(0, description="Result offset")
    artists: Optional[List[Artist]] = Field(None, description="Artist results")
    releases: Optional[List[Release]] = Field(None, description="Release results")
    recordings: Optional[List[Recording]] = Field(None, description="Recording results")
    release_groups: Optional[List[ReleaseGroup]] = Field(None, alias="release-groups", description="Release group results")
    labels: Optional[List[Label]] = Field(None, description="Label results")
    works: Optional[List[Work]] = Field(None, description="Work results")
