"""
Mock API response data for testing MusicBrainz MCP server.

This module contains realistic mock data that mimics actual MusicBrainz API responses
for use in unit tests and integration tests.
"""

from typing import Dict, Any, List


# Artist mock data
MOCK_ARTIST_BEATLES = {
    "id": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
    "name": "The Beatles",
    "sort-name": "Beatles, The",
    "disambiguation": "",
    "type": "Group",
    "type-id": "e431f5f6-b5d2-343d-8b36-72607fffb74b",
    "gender": None,
    "country": "GB",
    "life-span": {
        "begin": "1960",
        "end": "1970",
        "ended": True
    },
    "area": {
        "id": "8a754a16-0027-3a29-b6d7-2b40ea0481ed",
        "name": "United Kingdom",
        "sort-name": "United Kingdom",
        "iso-3166-1-codes": ["GB"]
    },
    "aliases": [
        {
            "name": "Beatles",
            "sort-name": "Beatles",
            "type": "Artist name",
            "primary": True,
            "locale": "en"
        }
    ],
    "tags": [
        {"name": "rock", "count": 15},
        {"name": "pop", "count": 12},
        {"name": "british", "count": 8}
    ]
}

MOCK_ARTIST_DYLAN = {
    "id": "72c536dc-7137-4477-a521-567eeb840fa8",
    "name": "Bob Dylan",
    "sort-name": "Dylan, Bob",
    "disambiguation": "",
    "type": "Person",
    "type-id": "b6e035f4-3ce9-331c-97df-83397230b0df",
    "gender": "Male",
    "country": "US",
    "life-span": {
        "begin": "1941-05-24",
        "end": None,
        "ended": False
    },
    "area": {
        "id": "489ce91b-6658-3307-9877-795b68554c98",
        "name": "United States",
        "sort-name": "United States",
        "iso-3166-1-codes": ["US"]
    }
}

# Release mock data
MOCK_RELEASE_ABBEY_ROAD = {
    "id": "f4a261d1-2a31-4d1a-b4b6-7d6e4c8f9a0b",
    "title": "Abbey Road",
    "disambiguation": "",
    "date": "1969-09-26",
    "country": "GB",
    "status": "Official",
    "status-id": "4e304316-386d-3409-af2e-78857eec5cfe",
    "packaging": "None",
    "barcode": "077774644020",
    "text-representation": {
        "language": "eng",
        "script": "Latn"
    },
    "artist-credit": [
        {
            "name": "The Beatles",
            "joinphrase": "",
            "artist": {
                "id": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
                "name": "The Beatles",
                "sort-name": "Beatles, The",
                "disambiguation": ""
            }
        }
    ],
    "release-group": {
        "id": "1c205925-2cfe-35c0-81de-d7ef17df9658",
        "title": "Abbey Road",
        "primary-type": "Album"
    },
    "media": [
        {
            "position": 1,
            "title": "",
            "format": "CD",
            "track-count": 17,
            "tracks": [
                {
                    "id": "track1",
                    "position": 1,
                    "title": "Come Together",
                    "length": 259000,
                    "number": "1"
                },
                {
                    "id": "track2", 
                    "position": 2,
                    "title": "Something",
                    "length": 182000,
                    "number": "2"
                }
            ]
        }
    ]
}

# Recording mock data
MOCK_RECORDING_COME_TOGETHER = {
    "id": "c1a2b3d4-e5f6-7890-abcd-ef1234567890",
    "title": "Come Together",
    "disambiguation": "",
    "length": 259000,
    "video": False,
    "artist-credit": [
        {
            "name": "The Beatles",
            "joinphrase": "",
            "artist": {
                "id": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
                "name": "The Beatles",
                "sort-name": "Beatles, The"
            }
        }
    ],
    "isrcs": ["GBUM71505078"],
    "releases": [
        {
            "id": "f4a261d1-2a31-4d1a-b4b6-7d6e4c8f9a0b",
            "title": "Abbey Road",
            "date": "1969-09-26"
        }
    ]
}

# Release Group mock data
MOCK_RELEASE_GROUP_ABBEY_ROAD = {
    "id": "1c205925-2cfe-35c0-81de-d7ef17df9658",
    "title": "Abbey Road",
    "disambiguation": "",
    "primary-type": "Album",
    "primary-type-id": "f529b476-6e62-324f-b0aa-1f3e33d313fc",
    "secondary-types": [],
    "first-release-date": "1969-09-26",
    "artist-credit": [
        {
            "name": "The Beatles",
            "artist": {
                "id": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
                "name": "The Beatles",
                "sort-name": "Beatles, The"
            }
        }
    ]
}

# Search response mock data
MOCK_ARTIST_SEARCH_RESPONSE = {
    "created": "2023-01-01T00:00:00.000Z",
    "count": 177437,
    "offset": 0,
    "artists": [
        {
            "id": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
            "name": "The Beatles",
            "sort-name": "Beatles, The",
            "type": "Group",
            "country": "GB",
            "life-span": {"begin": "1960", "end": "1970", "ended": True},
            "score": 100,
            "tags": [{"name": "rock", "count": 15}]
        },
        {
            "id": "f54ba2b2-5a0e-4329-9e01-dc5d2c7b0e6f",
            "name": "The Beatles Revival Band",
            "sort-name": "Beatles Revival Band, The",
            "type": "Group",
            "score": 85
        }
    ]
}

MOCK_RELEASE_SEARCH_RESPONSE = {
    "created": "2023-01-01T00:00:00.000Z",
    "count": 1234,
    "offset": 0,
    "releases": [
        {
            "id": "f4a261d1-2a31-4d1a-b4b6-7d6e4c8f9a0b",
            "title": "Abbey Road",
            "date": "1969-09-26",
            "country": "GB",
            "status": "Official",
            "artist-credit": [{
                "name": "The Beatles",
                "artist": {
                    "id": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
                    "name": "The Beatles"
                }
            }],
            "score": 100
        }
    ]
}

MOCK_RECORDING_SEARCH_RESPONSE = {
    "created": "2023-01-01T00:00:00.000Z", 
    "count": 567,
    "offset": 0,
    "recordings": [
        {
            "id": "c1a2b3d4-e5f6-7890-abcd-ef1234567890",
            "title": "Come Together",
            "length": 259000,
            "artist-credit": [{
                "name": "The Beatles",
                "artist": {
                    "id": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
                    "name": "The Beatles"
                }
            }],
            "score": 100
        }
    ]
}

# Browse response mock data
MOCK_ARTIST_RELEASES_BROWSE_RESPONSE = {
    "release-count": 3106,
    "release-offset": 0,
    "releases": [
        {
            "id": "f4a261d1-2a31-4d1a-b4b6-7d6e4c8f9a0b",
            "title": "Abbey Road",
            "date": "1969-09-26",
            "status": "Official",
            "packaging": "None"
        },
        {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "title": "Let It Be",
            "date": "1970-05-08", 
            "status": "Official",
            "packaging": "None"
        }
    ]
}

MOCK_ARTIST_RECORDINGS_BROWSE_RESPONSE = {
    "recording-count": 1500,
    "recording-offset": 0,
    "recordings": [
        {
            "id": "c1a2b3d4-e5f6-7890-abcd-ef1234567890",
            "title": "Come Together",
            "length": 259000
        },
        {
            "id": "d2e3f4g5-h6i7-8901-bcde-f23456789012",
            "title": "Something",
            "length": 182000
        }
    ]
}

# Error response mock data
MOCK_ERROR_RESPONSE_404 = {
    "error": "Not Found",
    "help": "For usage, please see: https://musicbrainz.org/development/mmd"
}

MOCK_ERROR_RESPONSE_400 = {
    "error": "Bad Request",
    "help": "Invalid query parameters"
}

MOCK_ERROR_RESPONSE_503 = {
    "error": "Service Unavailable",
    "help": "The server is temporarily unavailable"
}

# Rate limit response
MOCK_RATE_LIMIT_RESPONSE = {
    "error": "Your requests are exceeding the allowable rate limit. Please see https://musicbrainz.org/doc/XML_Web_Service/Rate_Limiting for more information."
}


def get_mock_response_by_entity_and_id(entity_type: str, entity_id: str) -> Dict[str, Any]:
    """
    Get mock response data by entity type and ID.
    
    Args:
        entity_type: Type of entity (artist, release, recording, etc.)
        entity_id: Entity ID
        
    Returns:
        Mock response data
    """
    mock_data_map = {
        "artist": {
            "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d": MOCK_ARTIST_BEATLES,
            "72c536dc-7137-4477-a521-567eeb840fa8": MOCK_ARTIST_DYLAN,
        },
        "release": {
            "f4a261d1-2a31-4d1a-b4b6-7d6e4c8f9a0b": MOCK_RELEASE_ABBEY_ROAD,
        },
        "recording": {
            "c1a2b3d4-e5f6-7890-abcd-ef1234567890": MOCK_RECORDING_COME_TOGETHER,
        },
        "release-group": {
            "1c205925-2cfe-35c0-81de-d7ef17df9658": MOCK_RELEASE_GROUP_ABBEY_ROAD,
        }
    }
    
    return mock_data_map.get(entity_type, {}).get(entity_id, {})


def get_mock_search_response(entity_type: str, query: str = "") -> Dict[str, Any]:
    """
    Get mock search response by entity type.
    
    Args:
        entity_type: Type of entity to search
        query: Search query (for filtering mock data)
        
    Returns:
        Mock search response
    """
    search_responses = {
        "artist": MOCK_ARTIST_SEARCH_RESPONSE,
        "release": MOCK_RELEASE_SEARCH_RESPONSE,
        "recording": MOCK_RECORDING_SEARCH_RESPONSE,
    }
    
    return search_responses.get(entity_type, {"count": 0, "offset": 0, f"{entity_type}s": []})


def get_mock_browse_response(entity_type: str, browse_type: str) -> Dict[str, Any]:
    """
    Get mock browse response.
    
    Args:
        entity_type: Type of entity being browsed
        browse_type: Type of browse operation
        
    Returns:
        Mock browse response
    """
    if entity_type == "release" and browse_type == "artist":
        return MOCK_ARTIST_RELEASES_BROWSE_RESPONSE
    elif entity_type == "recording" and browse_type == "artist":
        return MOCK_ARTIST_RECORDINGS_BROWSE_RESPONSE
    
    return {"count": 0, "offset": 0, f"{entity_type}s": []}
