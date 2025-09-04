# MusicBrainz MCP Server - API Reference

This document provides comprehensive documentation for all MCP tools available in the MusicBrainz MCP Server.

## Overview

The MusicBrainz MCP Server provides 10 tools for querying the MusicBrainz database:

- **Search Tools**: Find entities by name/query
- **Detail Tools**: Get comprehensive information by MBID
- **Browse Tools**: List related entities
- **Lookup Tool**: Generic entity lookup

## Authentication & Rate Limiting

- **No authentication required** for MusicBrainz API
- **Rate limiting**: 1 request per second (configurable)
- **User Agent**: Required (set via `MUSICBRAINZ_USER_AGENT`)

---

## Search Tools

### search_artist

Search for artists by name or query.

**Parameters:**
- `query` (string, required): Search query for artist name
- `limit` (integer, optional): Maximum results to return (1-100, default: 25)
- `offset` (integer, optional): Number of results to skip (default: 0)

**Example:**
```json
{
  "params": {
    "query": "The Beatles",
    "limit": 10,
    "offset": 0
  }
}
```

**Response:**
```json
{
  "count": 1234,
  "offset": 0,
  "artists": [
    {
      "id": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
      "name": "The Beatles",
      "sort_name": "Beatles, The",
      "type": "Group",
      "country": "GB",
      "life_span": {
        "begin": "1960",
        "end": "1970"
      },
      "score": 100
    }
  ]
}
```

### search_release

Search for releases (albums) by name or query.

**Parameters:**
- `query` (string, required): Search query for release name
- `limit` (integer, optional): Maximum results to return (1-100, default: 25)
- `offset` (integer, optional): Number of results to skip (default: 0)

**Example:**
```json
{
  "params": {
    "query": "Abbey Road",
    "limit": 5
  }
}
```

**Response:**
```json
{
  "count": 567,
  "offset": 0,
  "releases": [
    {
      "id": "f4a261d1-2a31-4d1a-b4b6-7d6e4c8f9a0b",
      "title": "Abbey Road",
      "date": "1969-09-26",
      "country": "GB",
      "status": "Official",
      "artist_credit": [
        {
          "name": "The Beatles",
          "artist": {
            "id": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
            "name": "The Beatles"
          }
        }
      ],
      "score": 100
    }
  ]
}
```

### search_recording

Search for individual recordings (songs) by name or query.

**Parameters:**
- `query` (string, required): Search query for recording name
- `limit` (integer, optional): Maximum results to return (1-100, default: 25)
- `offset` (integer, optional): Number of results to skip (default: 0)

**Example:**
```json
{
  "params": {
    "query": "Come Together",
    "limit": 10
  }
}
```

### search_release_group

Search for release groups by name or query.

**Parameters:**
- `query` (string, required): Search query for release group name
- `limit` (integer, optional): Maximum results to return (1-100, default: 25)
- `offset` (integer, optional): Number of results to skip (default: 0)

**Example:**
```json
{
  "params": {
    "query": "Abbey Road",
    "limit": 5
  }
}
```

---

## Detail Tools

### get_artist_details

Get comprehensive information about an artist by MusicBrainz ID.

**Parameters:**
- `mbid` (string, required): MusicBrainz ID (UUID format)
- `inc` (array, optional): Additional data to include

**Available includes:**
- `releases`: Include artist's releases
- `recordings`: Include artist's recordings
- `release-groups`: Include release groups
- `works`: Include works
- `aliases`: Include aliases
- `tags`: Include tags
- `ratings`: Include ratings

**Example:**
```json
{
  "params": {
    "mbid": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
    "inc": ["releases", "recordings"]
  }
}
```

**Response:**
```json
{
  "id": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
  "name": "The Beatles",
  "sort_name": "Beatles, The",
  "type": "Group",
  "country": "GB",
  "life_span": {
    "begin": "1960",
    "end": "1970"
  },
  "releases": [...],
  "recordings": [...]
}
```

### get_release_details

Get comprehensive information about a release by MusicBrainz ID.

**Parameters:**
- `mbid` (string, required): MusicBrainz ID (UUID format)
- `inc` (array, optional): Additional data to include

**Available includes:**
- `recordings`: Include track recordings
- `artists`: Include artist information
- `labels`: Include label information
- `media`: Include media information

**Example:**
```json
{
  "params": {
    "mbid": "f4a261d1-2a31-4d1a-b4b6-7d6e4c8f9a0b",
    "inc": ["recordings", "artists"]
  }
}
```

### get_recording_details

Get comprehensive information about a recording by MusicBrainz ID.

**Parameters:**
- `mbid` (string, required): MusicBrainz ID (UUID format)
- `inc` (array, optional): Additional data to include

**Available includes:**
- `artists`: Include artist information
- `releases`: Include releases containing this recording
- `isrcs`: Include ISRC codes

**Example:**
```json
{
  "params": {
    "mbid": "c1a2b3d4-e5f6-7890-abcd-ef1234567890",
    "inc": ["artists", "releases"]
  }
}
```

---

## Browse Tools

### browse_artist_releases

Browse all releases by a specific artist.

**Parameters:**
- `artist_mbid` (string, required): Artist's MusicBrainz ID
- `limit` (integer, optional): Maximum results to return (1-100, default: 25)
- `offset` (integer, optional): Number of results to skip (default: 0)
- `release_type` (array, optional): Filter by release type
- `release_status` (array, optional): Filter by release status

**Release Types:**
- `album`, `single`, `ep`, `compilation`, `soundtrack`, `spokenword`, `interview`, `audiobook`, `live`, `remix`, `other`

**Release Statuses:**
- `official`, `promotion`, `bootleg`, `pseudo-release`

**Example:**
```json
{
  "params": {
    "artist_mbid": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
    "limit": 20,
    "release_type": ["album"],
    "release_status": ["official"]
  }
}
```

### browse_artist_recordings

Browse all recordings by a specific artist.

**Parameters:**
- `artist_mbid` (string, required): Artist's MusicBrainz ID
- `limit` (integer, optional): Maximum results to return (1-100, default: 25)
- `offset` (integer, optional): Number of results to skip (default: 0)

**Example:**
```json
{
  "params": {
    "artist_mbid": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
    "limit": 50
  }
}
```

---

## Generic Lookup Tool

### lookup_by_mbid

Generic lookup tool for any MusicBrainz entity by ID.

**Parameters:**
- `entity_type` (string, required): Type of entity to lookup
- `mbid` (string, required): MusicBrainz ID (UUID format)
- `inc` (array, optional): Additional data to include

**Entity Types:**
- `artist`, `release`, `recording`, `release-group`, `work`, `label`, `area`

**Example:**
```json
{
  "params": {
    "entity_type": "artist",
    "mbid": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
    "inc": ["releases"]
  }
}
```

---

## Error Handling

### Common Error Responses

**Validation Error:**
```json
{
  "error": "ValidationError",
  "message": "Invalid MBID format",
  "details": "MBID must be a valid UUID"
}
```

**Rate Limit Error:**
```json
{
  "error": "MusicBrainzRateLimitError",
  "message": "Rate limit exceeded",
  "retry_after": 60
}
```

**API Error:**
```json
{
  "error": "MusicBrainzAPIError",
  "message": "HTTP 404 error",
  "status_code": 404
}
```

### Error Codes

- `400`: Bad Request (invalid parameters)
- `404`: Not Found (entity doesn't exist)
- `429`: Too Many Requests (rate limit exceeded)
- `503`: Service Unavailable (MusicBrainz API down)

---

## Best Practices

1. **Use specific queries** for better search results
2. **Implement pagination** for large result sets
3. **Cache results** when possible to reduce API calls
4. **Handle rate limits** gracefully with exponential backoff
5. **Validate MBIDs** before making lookup requests
6. **Use includes sparingly** to avoid large responses

## Rate Limiting

- **Default**: 1 request per second
- **Configurable**: Set `MUSICBRAINZ_RATE_LIMIT` environment variable
- **Recommendation**: Don't exceed 1 req/sec for public instances
- **Commercial**: Contact MusicBrainz for higher limits

## Data Freshness

- **Real-time**: All data comes directly from MusicBrainz API
- **No local cache**: Data is always current
- **Updates**: Reflects MusicBrainz database updates immediately
