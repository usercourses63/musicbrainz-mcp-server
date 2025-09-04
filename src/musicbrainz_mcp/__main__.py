"""
Main entry point for the MusicBrainz MCP Server module.
This allows running the server with: python -m musicbrainz_mcp
"""

from .server import main

if __name__ == "__main__":
    main()
