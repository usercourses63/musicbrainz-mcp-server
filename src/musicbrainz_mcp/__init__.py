"""
MusicBrainz MCP Server

A Model Context Protocol (MCP) server for querying the MusicBrainz database.
Provides comprehensive music metadata access including artists, albums, recordings,
releases, and related information through a standardized MCP interface.
"""

__version__ = "0.1.0"
__author__ = "MusicBrainz MCP Team"
__email__ = "contact@example.com"
__description__ = "MCP Server for querying the MusicBrainz database"

# Public API exports
from .musicbrainz_client import MusicBrainzClient

# Import server and models when they're available
try:
    from .server import create_server, main, mcp
    _server_available = True
except ImportError:
    _server_available = False

try:
    from .utils import (
        MBIDUtils, ResponseFormatter, QueryUtils, CacheUtils,
        PaginationUtils, URLUtils, LoggingUtils, DataUtils, get_cache
    )
    from .config import (
        MusicBrainzMCPConfig, APIConfig, CacheConfig, LoggingConfig, ServerConfig,
        get_config, set_config, load_config_from_file
    )
    _utils_available = True
except ImportError:
    _utils_available = False

try:
    from .models import (
        Artist,
        Release,
        Recording,
        ReleaseGroup,
        Label,
        Work,
        SearchResult,
    )
    _models_available = True
except ImportError:
    _models_available = False

# Build __all__ dynamically based on what's available
__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    "MusicBrainzClient",
]

if _server_available:
    __all__.extend(["create_server", "main", "mcp"])

if _models_available:
    __all__.extend([
        "Artist",
        "Release",
        "Recording",
        "ReleaseGroup",
        "Label",
        "Work",
        "SearchResult",
    ])

if _utils_available:
    __all__.extend([
        "MBIDUtils",
        "ResponseFormatter",
        "QueryUtils",
        "CacheUtils",
        "PaginationUtils",
        "URLUtils",
        "LoggingUtils",
        "DataUtils",
        "get_cache",
        "MusicBrainzMCPConfig",
        "APIConfig",
        "CacheConfig",
        "LoggingConfig",
        "ServerConfig",
        "get_config",
        "set_config",
        "load_config_from_file",
    ])
