# Usage Examples

This document provides practical examples of using the MusicBrainz MCP Server with various MCP clients.

## Table of Contents

- [Basic Setup](#basic-setup)
- [Search Examples](#search-examples)
- [Detail Lookup Examples](#detail-lookup-examples)
- [Browse Examples](#browse-examples)
- [Advanced Use Cases](#advanced-use-cases)
- [Integration Examples](#integration-examples)

## Basic Setup

### Starting the Server

```bash
# Set required configuration
export MUSICBRAINZ_USER_AGENT="MyApp/1.0.0 (user@example.com)"

# Start the server
python -m musicbrainz_mcp.main
```

### Connecting with FastMCP Client

```python
from fastmcp import Client
from musicbrainz_mcp.server import create_server

# Create server and client
server = create_server()
async with Client(server) as client:
    # Use client for queries
    result = await client.call_tool("search_artist", {
        "params": {"query": "The Beatles"}
    })
```

## Search Examples

### 1. Basic Artist Search

Find artists by name:

```python
async def search_artists_example():
    result = await client.call_tool("search_artist", {
        "params": {
            "query": "The Beatles",
            "limit": 10
        }
    })
    
    print(f"Found {result['count']} artists")
    for artist in result['artists']:
        print(f"- {artist['name']} ({artist['id']})")
```

### 2. Advanced Artist Search

Search with specific criteria:

```python
async def advanced_artist_search():
    # Search for jazz artists from the US
    result = await client.call_tool("search_artist", {
        "params": {
            "query": "country:US AND tag:jazz",
            "limit": 20
        }
    })
    
    for artist in result['artists']:
        print(f"{artist['name']} - {artist.get('country', 'Unknown')}")
```

### 3. Release Search

Find albums/releases:

```python
async def search_releases_example():
    result = await client.call_tool("search_release", {
        "params": {
            "query": "Abbey Road",
            "limit": 5
        }
    })
    
    for release in result['releases']:
        artist_name = release['artist_credit'][0]['name']
        print(f"{release['title']} by {artist_name} ({release['date']})")
```

### 4. Recording Search

Find individual songs:

```python
async def search_recordings_example():
    result = await client.call_tool("search_recording", {
        "params": {
            "query": "Come Together",
            "limit": 10
        }
    })
    
    for recording in result['recordings']:
        artist_name = recording['artist_credit'][0]['name']
        print(f"{recording['title']} by {artist_name}")
        if 'length' in recording:
            duration = recording['length'] // 1000  # Convert to seconds
            print(f"  Duration: {duration//60}:{duration%60:02d}")
```

## Detail Lookup Examples

### 1. Artist Details with Discography

Get comprehensive artist information:

```python
async def get_artist_with_discography():
    beatles_mbid = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
    
    result = await client.call_tool("get_artist_details", {
        "params": {
            "mbid": beatles_mbid,
            "inc": ["releases", "release-groups"]
        }
    })
    
    print(f"Artist: {result['name']}")
    print(f"Type: {result['type']}")
    print(f"Country: {result['country']}")
    print(f"Active: {result['life_span']['begin']} - {result['life_span']['end']}")
    
    if 'releases' in result:
        print(f"\nReleases ({len(result['releases'])}):")
        for release in result['releases'][:10]:  # Show first 10
            print(f"- {release['title']} ({release.get('date', 'Unknown')})")
```

### 2. Release Details with Track Listing

Get album information with tracks:

```python
async def get_release_with_tracks():
    abbey_road_mbid = "f4a261d1-2a31-4d1a-b4b6-7d6e4c8f9a0b"
    
    result = await client.call_tool("get_release_details", {
        "params": {
            "mbid": abbey_road_mbid,
            "inc": ["recordings", "media"]
        }
    })
    
    print(f"Release: {result['title']}")
    print(f"Date: {result['date']}")
    print(f"Country: {result['country']}")
    
    if 'media' in result:
        for medium in result['media']:
            print(f"\n{medium['format']} - {medium['title']}")
            for track in medium['tracks']:
                print(f"  {track['position']}. {track['title']}")
```

### 3. Recording Details

Get detailed song information:

```python
async def get_recording_details():
    come_together_mbid = "c1a2b3d4-e5f6-7890-abcd-ef1234567890"
    
    result = await client.call_tool("get_recording_details", {
        "params": {
            "mbid": come_together_mbid,
            "inc": ["artists", "releases", "isrcs"]
        }
    })
    
    print(f"Recording: {result['title']}")
    if 'length' in result:
        duration = result['length'] // 1000
        print(f"Duration: {duration//60}:{duration%60:02d}")
    
    print("Artists:")
    for credit in result['artist_credit']:
        print(f"- {credit['name']}")
    
    if 'isrcs' in result:
        print(f"ISRCs: {', '.join(result['isrcs'])}")
```

## Browse Examples

### 1. Browse Artist Releases

List all releases by an artist:

```python
async def browse_artist_releases():
    beatles_mbid = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
    
    # Get only official studio albums
    result = await client.call_tool("browse_artist_releases", {
        "params": {
            "artist_mbid": beatles_mbid,
            "limit": 50,
            "release_type": ["album"],
            "release_status": ["official"]
        }
    })
    
    print(f"Official Albums ({result['count']}):")
    for release in result['releases']:
        print(f"- {release['title']} ({release.get('date', 'Unknown')})")
```

### 2. Browse Artist Recordings

List all songs by an artist:

```python
async def browse_artist_recordings():
    beatles_mbid = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
    
    result = await client.call_tool("browse_artist_recordings", {
        "params": {
            "artist_mbid": beatles_mbid,
            "limit": 100
        }
    })
    
    print(f"Recordings ({result['count']}):")
    for recording in result['recordings']:
        print(f"- {recording['title']}")
        if 'length' in recording:
            duration = recording['length'] // 1000
            print(f"  ({duration//60}:{duration%60:02d})")
```

## Advanced Use Cases

### 1. Music Discovery Workflow

Find similar artists and their popular releases:

```python
async def music_discovery_workflow():
    # Start with a known artist
    search_result = await client.call_tool("search_artist", {
        "params": {"query": "Radiohead", "limit": 1}
    })
    
    if search_result['artists']:
        artist = search_result['artists'][0]
        artist_mbid = artist['id']
        
        # Get their releases
        releases = await client.call_tool("browse_artist_releases", {
            "params": {
                "artist_mbid": artist_mbid,
                "limit": 10,
                "release_type": ["album"],
                "release_status": ["official"]
            }
        })
        
        print(f"Top albums by {artist['name']}:")
        for release in releases['releases']:
            print(f"- {release['title']} ({release.get('date', 'Unknown')})")
```

### 2. Discography Analysis

Analyze an artist's career timeline:

```python
async def analyze_discography():
    beatles_mbid = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
    
    # Get all official studio albums
    result = await client.call_tool("browse_artist_releases", {
        "params": {
            "artist_mbid": beatles_mbid,
            "limit": 100,
            "release_type": ["album"],
            "release_status": ["official"]
        }
    })
    
    # Sort by date and analyze
    releases_with_dates = [
        r for r in result['releases'] 
        if r.get('date') and len(r['date']) >= 4
    ]
    
    releases_with_dates.sort(key=lambda x: x['date'])
    
    print("Career Timeline:")
    for release in releases_with_dates:
        year = release['date'][:4]
        print(f"{year}: {release['title']}")
```

### 3. Track Duration Analysis

Analyze song lengths for an artist:

```python
async def analyze_track_durations():
    artist_mbid = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
    
    result = await client.call_tool("browse_artist_recordings", {
        "params": {
            "artist_mbid": artist_mbid,
            "limit": 200
        }
    })
    
    durations = []
    for recording in result['recordings']:
        if 'length' in recording and recording['length']:
            duration_seconds = recording['length'] // 1000
            durations.append(duration_seconds)
    
    if durations:
        avg_duration = sum(durations) / len(durations)
        print(f"Average song length: {avg_duration//60:.0f}:{avg_duration%60:02.0f}")
        print(f"Shortest song: {min(durations)//60:.0f}:{min(durations)%60:02.0f}")
        print(f"Longest song: {max(durations)//60:.0f}:{max(durations)%60:02.0f}")
```

## Integration Examples

### 1. Claude Desktop Integration

Configure Claude Desktop to use the MusicBrainz MCP Server:

```json
{
  "mcpServers": {
    "musicbrainz": {
      "command": "python",
      "args": ["-m", "musicbrainz_mcp.main"],
      "env": {
        "MUSICBRAINZ_USER_AGENT": "ClaudeDesktop/1.0.0"
      }
    }
  }
}
```

### 2. Custom MCP Client

Create a custom client for specific use cases:

```python
import asyncio
from fastmcp import Client
from musicbrainz_mcp.server import create_server

class MusicBrainzClient:
    def __init__(self):
        self.server = create_server()
        self.client = None
    
    async def __aenter__(self):
        self.client = Client(self.server)
        await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def find_artist_by_name(self, name):
        result = await self.client.call_tool("search_artist", {
            "params": {"query": name, "limit": 1}
        })
        return result['artists'][0] if result['artists'] else None
    
    async def get_artist_albums(self, artist_mbid):
        result = await self.client.call_tool("browse_artist_releases", {
            "params": {
                "artist_mbid": artist_mbid,
                "release_type": ["album"],
                "release_status": ["official"]
            }
        })
        return result['releases']

# Usage
async def main():
    async with MusicBrainzClient() as mb:
        artist = await mb.find_artist_by_name("The Beatles")
        if artist:
            albums = await mb.get_artist_albums(artist['id'])
            print(f"Found {len(albums)} albums by {artist['name']}")

asyncio.run(main())
```

### 3. Web API Wrapper

Create a REST API wrapper:

```python
from fastapi import FastAPI, HTTPException
from fastmcp import Client
from musicbrainz_mcp.server import create_server

app = FastAPI(title="MusicBrainz API Wrapper")
server = create_server()

@app.get("/artists/search")
async def search_artists(q: str, limit: int = 25):
    async with Client(server) as client:
        result = await client.call_tool("search_artist", {
            "params": {"query": q, "limit": limit}
        })
        return result

@app.get("/artists/{mbid}")
async def get_artist(mbid: str, inc: str = ""):
    includes = inc.split(",") if inc else []
    async with Client(server) as client:
        try:
            result = await client.call_tool("get_artist_details", {
                "params": {"mbid": mbid, "inc": includes}
            })
            return result
        except Exception as e:
            raise HTTPException(status_code=404, detail=str(e))

# Run with: uvicorn wrapper:app --reload
```

## Error Handling Examples

### 1. Graceful Error Handling

```python
async def robust_search(query):
    try:
        result = await client.call_tool("search_artist", {
            "params": {"query": query, "limit": 10}
        })
        return result
    except Exception as e:
        if "rate limit" in str(e).lower():
            print("Rate limit exceeded, waiting...")
            await asyncio.sleep(60)
            return await robust_search(query)  # Retry
        elif "timeout" in str(e).lower():
            print("Request timeout, trying with shorter timeout...")
            # Could implement retry with different parameters
            return None
        else:
            print(f"Unexpected error: {e}")
            return None
```

### 2. Batch Processing with Rate Limiting

```python
async def batch_artist_lookup(artist_names):
    results = []
    
    for i, name in enumerate(artist_names):
        try:
            result = await client.call_tool("search_artist", {
                "params": {"query": name, "limit": 1}
            })
            results.append(result)
            
            # Respect rate limiting
            if i < len(artist_names) - 1:
                await asyncio.sleep(1.1)  # Slightly more than 1 second
                
        except Exception as e:
            print(f"Error searching for {name}: {e}")
            results.append(None)
    
    return results
```

## Performance Optimization Examples

### 1. Caching Results

```python
import json
from pathlib import Path

class CachedMusicBrainzClient:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.client = None
    
    def _cache_key(self, tool_name, params):
        return f"{tool_name}_{hash(json.dumps(params, sort_keys=True))}.json"
    
    async def call_tool_cached(self, tool_name, params):
        cache_file = self.cache_dir / self._cache_key(tool_name, params)
        
        # Check cache first
        if cache_file.exists():
            with open(cache_file) as f:
                return json.load(f)
        
        # Make API call
        result = await self.client.call_tool(tool_name, params)
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(result, f)
        
        return result
```

### 2. Parallel Requests

```python
async def parallel_artist_details(artist_mbids):
    async def get_single_artist(mbid):
        return await client.call_tool("get_artist_details", {
            "params": {"mbid": mbid}
        })
    
    # Create tasks for parallel execution
    tasks = [get_single_artist(mbid) for mbid in artist_mbids]
    
    # Execute with rate limiting (max 1 per second)
    results = []
    for task in tasks:
        result = await task
        results.append(result)
        await asyncio.sleep(1.1)  # Rate limiting
    
    return results
```

These examples demonstrate the flexibility and power of the MusicBrainz MCP Server for various music-related applications and integrations.
