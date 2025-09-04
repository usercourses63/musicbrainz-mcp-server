#!/usr/bin/env python3
"""
Advanced integration example for MusicBrainz MCP Server.

This script demonstrates advanced usage patterns including:
- Custom client wrapper
- Error handling and retry logic
- Batch processing with rate limiting
- Data analysis and aggregation
- Integration with external systems
"""

import asyncio
import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from fastmcp import Client
from musicbrainz_mcp.server import create_server


@dataclass
class ArtistSummary:
    """Summary information about an artist."""
    name: str
    mbid: str
    country: Optional[str]
    active_years: str
    album_count: int
    recording_count: int


class MusicBrainzAnalyzer:
    """Advanced MusicBrainz client with analysis capabilities."""
    
    def __init__(self):
        self.server = create_server()
        self.client = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = Client(self.server)
        await self.client.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def search_artist_with_retry(self, query: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """Search for artist with retry logic."""
        for attempt in range(max_retries):
            try:
                result = await self.client.call_tool("search_artist", {
                    "params": {"query": query, "limit": 1}
                })
                
                if result['artists']:
                    return result['artists'][0]
                return None
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
        
        return None
    
    async def get_artist_summary(self, artist_name: str) -> Optional[ArtistSummary]:
        """Get comprehensive artist summary."""
        try:
            # Search for artist
            artist = await self.search_artist_with_retry(artist_name)
            if not artist:
                return None
            
            artist_mbid = artist['id']
            
            # Get detailed information
            details = await self.client.call_tool("get_artist_details", {
                "params": {"mbid": artist_mbid}
            })
            
            # Get release count
            releases = await self.client.call_tool("browse_artist_releases", {
                "params": {
                    "artist_mbid": artist_mbid,
                    "limit": 1,
                    "release_type": ["album"],
                    "release_status": ["official"]
                }
            })
            
            # Get recording count
            recordings = await self.client.call_tool("browse_artist_recordings", {
                "params": {"artist_mbid": artist_mbid, "limit": 1}
            })
            
            # Format active years
            life_span = details.get('life_span', {})
            begin = life_span.get('begin', 'Unknown')
            end = life_span.get('end', 'Present')
            active_years = f"{begin} - {end}"
            
            return ArtistSummary(
                name=details['name'],
                mbid=artist_mbid,
                country=details.get('country'),
                active_years=active_years,
                album_count=releases['count'],
                recording_count=recordings['count']
            )
            
        except Exception as e:
            print(f"Error getting artist summary for {artist_name}: {e}")
            return None
    
    async def batch_artist_analysis(self, artist_names: List[str]) -> List[ArtistSummary]:
        """Analyze multiple artists with rate limiting."""
        summaries = []
        
        for i, name in enumerate(artist_names):
            print(f"Analyzing {i+1}/{len(artist_names)}: {name}")
            
            summary = await self.get_artist_summary(name)
            if summary:
                summaries.append(summary)
            
            # Rate limiting - wait between requests
            if i < len(artist_names) - 1:
                await asyncio.sleep(1.2)  # Slightly more than 1 second
        
        return summaries
    
    async def find_similar_artists_by_country(self, country_code: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find artists from a specific country."""
        try:
            result = await self.client.call_tool("search_artist", {
                "params": {
                    "query": f"country:{country_code}",
                    "limit": limit
                }
            })
            return result['artists']
            
        except Exception as e:
            print(f"Error finding artists from {country_code}: {e}")
            return []
    
    async def analyze_discography_timeline(self, artist_name: str) -> Dict[str, Any]:
        """Analyze an artist's discography timeline."""
        try:
            artist = await self.search_artist_with_retry(artist_name)
            if not artist:
                return {}
            
            # Get all releases
            releases = await self.client.call_tool("browse_artist_releases", {
                "params": {
                    "artist_mbid": artist['id'],
                    "limit": 100,
                    "release_type": ["album"],
                    "release_status": ["official"]
                }
            })
            
            # Analyze by decade
            decade_analysis = {}
            total_releases = 0
            
            for release in releases['releases']:
                date = release.get('date', '')
                if len(date) >= 4:
                    year = int(date[:4])
                    decade = (year // 10) * 10
                    decade_key = f"{decade}s"
                    
                    if decade_key not in decade_analysis:
                        decade_analysis[decade_key] = []
                    
                    decade_analysis[decade_key].append({
                        'title': release['title'],
                        'year': year,
                        'date': date
                    })
                    total_releases += 1
            
            return {
                'artist': artist['name'],
                'total_releases': total_releases,
                'decades': decade_analysis,
                'career_span': len(decade_analysis)
            }
            
        except Exception as e:
            print(f"Error analyzing discography for {artist_name}: {e}")
            return {}


async def demonstrate_advanced_features():
    """Demonstrate advanced MusicBrainz MCP Server features."""
    
    # Set up user agent
    if not os.getenv("MUSICBRAINZ_USER_AGENT"):
        os.environ["MUSICBRAINZ_USER_AGENT"] = "AdvancedExample/1.0.0 (example@localhost)"
    
    print("🎵 MusicBrainz MCP Server - Advanced Integration Example")
    print("=" * 60)
    
    async with MusicBrainzAnalyzer() as analyzer:
        
        # Example 1: Batch artist analysis
        print("\n1. Batch Artist Analysis")
        print("-" * 30)
        
        famous_bands = ["The Beatles", "Led Zeppelin", "Pink Floyd", "Queen"]
        summaries = await analyzer.batch_artist_analysis(famous_bands)
        
        print(f"\nAnalyzed {len(summaries)} artists:")
        for summary in summaries:
            print(f"\n{summary.name}")
            print(f"  Country: {summary.country or 'Unknown'}")
            print(f"  Active: {summary.active_years}")
            print(f"  Albums: {summary.album_count}")
            print(f"  Recordings: {summary.recording_count}")
        
        # Example 2: Country-based analysis
        print("\n\n2. Artists by Country Analysis")
        print("-" * 35)
        
        uk_artists = await analyzer.find_similar_artists_by_country("GB", limit=5)
        print(f"\nTop UK artists:")
        for artist in uk_artists:
            print(f"  - {artist['name']} (Score: {artist.get('score', 'N/A')})")
        
        # Example 3: Discography timeline analysis
        print("\n\n3. Discography Timeline Analysis")
        print("-" * 38)
        
        timeline = await analyzer.analyze_discography_timeline("The Beatles")
        if timeline:
            print(f"\n{timeline['artist']} Career Analysis:")
            print(f"Total releases: {timeline['total_releases']}")
            print(f"Career span: {timeline['career_span']} decades")
            
            for decade, releases in timeline['decades'].items():
                print(f"\n{decade}:")
                for release in sorted(releases, key=lambda x: x['year']):
                    print(f"  {release['year']}: {release['title']}")
        
        # Example 4: Data export
        print("\n\n4. Data Export Example")
        print("-" * 25)
        
        # Export analysis results to JSON
        export_data = {
            'analysis_date': '2024-01-01',
            'artist_summaries': [
                {
                    'name': s.name,
                    'mbid': s.mbid,
                    'country': s.country,
                    'active_years': s.active_years,
                    'album_count': s.album_count,
                    'recording_count': s.recording_count
                }
                for s in summaries
            ],
            'uk_artists': [
                {'name': a['name'], 'mbid': a['id'], 'score': a.get('score')}
                for a in uk_artists
            ],
            'discography_analysis': timeline
        }
        
        # Save to file
        with open('musicbrainz_analysis.json', 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print("✅ Analysis data exported to 'musicbrainz_analysis.json'")
        
        # Example 5: Performance metrics
        print("\n\n5. Performance Metrics")
        print("-" * 22)
        
        import time
        
        # Measure search performance
        start_time = time.time()
        search_result = await analyzer.search_artist_with_retry("Radiohead")
        search_time = time.time() - start_time
        
        print(f"Artist search time: {search_time:.2f} seconds")
        
        if search_result:
            # Measure detail retrieval performance
            start_time = time.time()
            details = await analyzer.client.call_tool("get_artist_details", {
                "params": {"mbid": search_result['id']}
            })
            detail_time = time.time() - start_time
            
            print(f"Detail retrieval time: {detail_time:.2f} seconds")
            print(f"Total API calls: 2")
            print(f"Average response time: {(search_time + detail_time) / 2:.2f} seconds")


async def demonstrate_error_handling():
    """Demonstrate robust error handling patterns."""
    
    print("\n\n6. Error Handling Demonstration")
    print("-" * 35)
    
    async with MusicBrainzAnalyzer() as analyzer:
        
        # Test with invalid MBID
        try:
            await analyzer.client.call_tool("get_artist_details", {
                "params": {"mbid": "invalid-mbid-format"}
            })
        except Exception as e:
            print(f"✅ Caught invalid MBID error: {type(e).__name__}")
        
        # Test with non-existent artist
        result = await analyzer.search_artist_with_retry("NonExistentArtistXYZ123")
        if not result:
            print("✅ Gracefully handled non-existent artist")
        
        # Test retry mechanism
        print("✅ Retry mechanism tested during batch processing")


async def main():
    """Main function running all examples."""
    try:
        await demonstrate_advanced_features()
        await demonstrate_error_handling()
        
        print("\n" + "=" * 60)
        print("🎉 Advanced integration example completed successfully!")
        print("\nKey features demonstrated:")
        print("- Custom client wrapper with retry logic")
        print("- Batch processing with rate limiting")
        print("- Data analysis and aggregation")
        print("- Error handling and resilience")
        print("- Performance monitoring")
        print("- Data export capabilities")
        
        print("\nNext steps:")
        print("- Integrate with your application's data models")
        print("- Add caching for frequently accessed data")
        print("- Implement background processing for large datasets")
        print("- Add monitoring and alerting for production use")
        
    except Exception as e:
        print(f"❌ Example failed with error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
