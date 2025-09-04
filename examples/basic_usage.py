#!/usr/bin/env python3
"""
Basic usage example for MusicBrainz MCP Server.

This script demonstrates how to use the MusicBrainz MCP Server
to search for artists, get detailed information, and browse releases.
"""

import asyncio
import os
from fastmcp import Client
from musicbrainz_mcp.server import create_server


async def main():
    """Main example function demonstrating MusicBrainz MCP Server usage."""
    
    # Set up user agent (required for MusicBrainz API)
    if not os.getenv("MUSICBRAINZ_USER_AGENT"):
        os.environ["MUSICBRAINZ_USER_AGENT"] = "ExampleApp/1.0.0 (example@localhost)"
    
    print("🎵 MusicBrainz MCP Server - Basic Usage Example")
    print("=" * 50)
    
    # Create server and client
    server = create_server()
    
    async with Client(server) as client:
        
        # Example 1: Search for artists
        print("\n1. Searching for 'The Beatles'...")
        try:
            result = await client.call_tool("search_artist", {
                "params": {
                    "query": "The Beatles",
                    "limit": 3
                }
            })
            
            print(f"Found {result['count']} artists:")
            for artist in result['artists']:
                print(f"  - {artist['name']} (ID: {artist['id']})")
                if 'country' in artist:
                    print(f"    Country: {artist['country']}")
                if 'life_span' in artist:
                    span = artist['life_span']
                    begin = span.get('begin', 'Unknown')
                    end = span.get('end', 'Present')
                    print(f"    Active: {begin} - {end}")
                print()
                
        except Exception as e:
            print(f"Error searching for artists: {e}")
        
        # Example 2: Get detailed artist information
        print("\n2. Getting detailed information for The Beatles...")
        try:
            # Use the known Beatles MBID
            beatles_mbid = "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
            
            result = await client.call_tool("get_artist_details", {
                "params": {
                    "mbid": beatles_mbid,
                    "inc": ["releases"]
                }
            })
            
            print(f"Artist: {result['name']}")
            print(f"Type: {result.get('type', 'Unknown')}")
            print(f"Country: {result.get('country', 'Unknown')}")
            
            if 'life_span' in result:
                span = result['life_span']
                begin = span.get('begin', 'Unknown')
                end = span.get('end', 'Present')
                print(f"Active: {begin} - {end}")
            
            if 'releases' in result:
                print(f"Number of releases: {len(result['releases'])}")
                
        except Exception as e:
            print(f"Error getting artist details: {e}")
        
        # Example 3: Browse artist releases
        print("\n3. Browsing Beatles albums...")
        try:
            result = await client.call_tool("browse_artist_releases", {
                "params": {
                    "artist_mbid": beatles_mbid,
                    "limit": 10,
                    "release_type": ["album"],
                    "release_status": ["official"]
                }
            })
            
            print(f"Official albums ({result['count']} total):")
            for release in result['releases']:
                title = release['title']
                date = release.get('date', 'Unknown date')
                print(f"  - {title} ({date})")
                
        except Exception as e:
            print(f"Error browsing releases: {e}")
        
        # Example 4: Search for a specific album
        print("\n4. Searching for 'Abbey Road' album...")
        try:
            result = await client.call_tool("search_release", {
                "params": {
                    "query": "Abbey Road",
                    "limit": 5
                }
            })
            
            print(f"Found {result['count']} releases:")
            for release in result['releases']:
                title = release['title']
                date = release.get('date', 'Unknown')
                artist_name = release['artist_credit'][0]['name']
                print(f"  - {title} by {artist_name} ({date})")
                
        except Exception as e:
            print(f"Error searching for releases: {e}")
        
        # Example 5: Search for a recording
        print("\n5. Searching for 'Come Together' recording...")
        try:
            result = await client.call_tool("search_recording", {
                "params": {
                    "query": "Come Together",
                    "limit": 3
                }
            })
            
            print(f"Found {result['count']} recordings:")
            for recording in result['recordings']:
                title = recording['title']
                artist_name = recording['artist_credit'][0]['name']
                print(f"  - {title} by {artist_name}")
                
                if 'length' in recording and recording['length']:
                    duration_ms = recording['length']
                    duration_sec = duration_ms // 1000
                    minutes = duration_sec // 60
                    seconds = duration_sec % 60
                    print(f"    Duration: {minutes}:{seconds:02d}")
                
        except Exception as e:
            print(f"Error searching for recordings: {e}")
        
        # Example 6: Generic lookup
        print("\n6. Generic lookup example...")
        try:
            result = await client.call_tool("lookup_by_mbid", {
                "params": {
                    "entity_type": "artist",
                    "mbid": beatles_mbid
                }
            })
            
            print(f"Lookup result: {result['name']} ({result['type']})")
            
        except Exception as e:
            print(f"Error with generic lookup: {e}")
    
    print("\n✅ Example completed successfully!")
    print("\nNext steps:")
    print("- Try modifying the search queries")
    print("- Explore different entity types (artist, release, recording)")
    print("- Check the API documentation for more advanced features")
    print("- Look at the configuration options for caching and rate limiting")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
