# Changelog

All notable changes to the MusicBrainz MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-01-04

### Added

#### Smithery.ai Platform Support
- **Smithery.ai Deployment**: Complete deployment configuration for smithery.ai platform
- **Container Runtime**: Docker container deployment with HTTP transport
- **Configuration Schema**: JSON schema for user agent, rate limiting, and timeout settings
- **Platform Integration**: Full MCP protocol compliance for browser-based clients

#### Enhanced CORS Configuration
- **Universal Browser Support**: All origins allowed for maximum compatibility
- **MCP Headers Exposed**: Enhanced header exposure including `mcp-session-id`, `mcp-protocol-version`, `x-mcp-server`, `x-request-id`
- **Preflight Optimization**: 24-hour cache for improved performance
- **Browser Compatibility**: Full support for smithery.ai and other web-based MCP clients

#### Comprehensive Testing Suite
- **100% Tool Coverage**: All 10 MCP tools tested and verified working
- **Real Data Testing**: Tested with popular songs from the last 5 years
- **FastMCP Client**: Custom test client for comprehensive tool validation
- **Performance Testing**: Response time validation (< 10ms for health checks)
- **Protocol Compliance**: Full MCP JSON-RPC 2.0 compliance verification

#### Popular Music Data Access
- **Recent Artists**: Taylor Swift, The Weeknd, Billie Eilish, Ed Sheeran
- **Hit Songs**: Blinding Lights, Bad Guy, Shape of You, …Ready for It?
- **Recent Albums**: Midnights, Folklore, and comprehensive catalog access
- **Comprehensive Coverage**: 2,294 releases and 2,562 recordings for Taylor Swift alone

### Fixed
- **Docker Port Configuration**: Fixed Dockerfile to expose port 8081 for smithery.ai compatibility
- **Session Management**: Improved MCP session handling for browser clients
- **Tool Parameter Structure**: Fixed parameter validation for proper MCP tool calls

### Changed
- **Deployment Target**: Optimized for smithery.ai platform deployment
- **Configuration**: Enhanced configuration schema with better validation
- **Documentation**: Updated with smithery.ai deployment instructions

### Performance
- **Tool Execution**: 1-3 seconds per MusicBrainz query
- **Container Startup**: 43.8 seconds build time
- **Success Rate**: 100% tool functionality (10/10 tools working)
- **Response Times**: Excellent performance for all operations

## [1.0.0] - 2024-01-XX

### Added

#### Core Features
- **FastMCP Server Implementation**: Complete MCP server using FastMCP framework
- **10 MCP Tools**: Comprehensive set of tools for MusicBrainz database queries
  - `search_artist`: Search for artists by name
  - `search_release`: Search for releases/albums
  - `search_recording`: Search for individual tracks
  - `search_release_group`: Search for release groups
  - `get_artist_details`: Get detailed artist information by MBID
  - `get_release_details`: Get detailed release information by MBID
  - `get_recording_details`: Get detailed recording information by MBID
  - `browse_artist_releases`: Browse all releases by an artist
  - `browse_artist_recordings`: Browse all recordings by an artist
  - `lookup_by_mbid`: Generic lookup tool for any entity type

#### MusicBrainz API Integration
- **Async HTTP Client**: High-performance async client using httpx
- **Rate Limiting**: Configurable rate limiting (default: 1 req/sec)
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Retry Logic**: Automatic retry for transient failures
- **User Agent Management**: Configurable user agent for API compliance

#### Data Models and Validation
- **Pydantic Models**: Complete data models for all MusicBrainz entities
- **Type Safety**: Full type hints throughout the codebase
- **Validation**: Input validation for all parameters
- **Serialization**: Proper JSON serialization/deserialization

#### Configuration System
- **Environment Variables**: Support for environment-based configuration
- **Config Files**: JSON configuration file support
- **Flexible Setup**: Multiple configuration methods with precedence
- **Validation**: Configuration validation on startup

#### Caching System
- **In-Memory Cache**: Fast in-memory caching with TTL
- **Configurable**: Adjustable cache size and TTL
- **Performance**: Significant performance improvement for repeated queries

#### Testing Infrastructure
- **Comprehensive Test Suite**: 101 tests with 99% pass rate
- **Unit Tests**: 87 unit tests covering all components
- **Integration Tests**: 13 integration tests with real API calls
- **Mock Testing**: Complete HTTP mocking for reliable testing
- **Async Testing**: Full async/await test compatibility
- **Real API Tests**: Live MusicBrainz API integration tests

### Documentation
- **Complete API Reference**: Detailed documentation for all 10 MCP tools
- **Configuration Guide**: Comprehensive configuration documentation
- **Usage Examples**: Practical examples and tutorials
- **Deployment Guide**: Multiple deployment options (Docker, K8s, Cloud)
- **Contributing Guide**: Developer contribution guidelines

### Deployment Support
- **Docker Support**: Complete Docker containerization
- **Docker Compose**: Development and production compose files
- **Kubernetes**: K8s deployment manifests
- **Cloud Ready**: Support for Heroku, AWS Lambda, Google Cloud Run, Azure
- **Systemd Service**: Linux service configuration
- **Reverse Proxy**: Nginx and Apache configuration examples

### Performance Features
- **Async Architecture**: Full async/await implementation
- **Connection Pooling**: Efficient HTTP connection management
- **Request Batching**: Support for batch operations
- **Memory Efficiency**: Optimized memory usage with caching

### Security Features
- **Input Validation**: Comprehensive input sanitization
- **Error Sanitization**: Safe error message handling
- **Rate Limiting**: Protection against API abuse
- **Non-root Execution**: Secure container execution

### Developer Experience
- **Type Hints**: Complete type annotation
- **Code Quality**: Black, isort, flake8, mypy integration
- **Pre-commit Hooks**: Automated code quality checks
- **Development Tools**: Hot reload and debug support

## [Unreleased]

### Planned Features
- **Metrics and Monitoring**: Prometheus metrics endpoint
- **Advanced Caching**: Redis cache backend option
- **Batch Operations**: Bulk query operations
- **GraphQL Support**: GraphQL query interface
- **WebSocket Support**: Real-time updates
- **Plugin System**: Extensible plugin architecture

### Known Issues
- One integration test skips due to async cleanup edge case (non-functional)
- Rate limiting could be more sophisticated for burst handling

## Development History

### Pre-1.0.0 Development Phases

#### Phase 1: Project Setup (Completed)
- Python project structure
- Dependency management
- Development environment

#### Phase 2: Core Implementation (Completed)
- MusicBrainz API client
- Data models and validation
- FastMCP server implementation

#### Phase 3: Testing and Quality (Completed)
- Comprehensive test suite
- Code quality tools
- Async test compatibility fixes

#### Phase 4: Documentation (Completed)
- API reference documentation
- Usage examples and guides
- Deployment documentation

## Technical Specifications

### Requirements
- **Python**: 3.8+
- **Dependencies**: FastMCP, httpx, pydantic, pytest
- **API**: MusicBrainz Web Service v2
- **Protocol**: Model Context Protocol (MCP)

### Performance Characteristics
- **Response Time**: <100ms for cached queries
- **Throughput**: 1 req/sec (configurable, respects MusicBrainz limits)
- **Memory Usage**: ~50MB base, scales with cache size
- **Startup Time**: <2 seconds

### Compatibility
- **MCP Clients**: Compatible with all MCP-compliant clients
- **Operating Systems**: Linux, macOS, Windows
- **Deployment**: Local, Docker, Kubernetes, Cloud platforms
- **Python Versions**: 3.8, 3.9, 3.10, 3.11, 3.12

## Migration Guide

### From Development to Production
1. Set production user agent in `MUSICBRAINZ_USER_AGENT`
2. Configure appropriate rate limiting
3. Enable caching for better performance
4. Set up monitoring and logging
5. Use reverse proxy for SSL termination

### Configuration Migration
- Environment variables take precedence over config files
- All configuration is backward compatible
- Default values provide sensible production settings

## Contributors

- Initial implementation and architecture
- Comprehensive testing infrastructure
- Documentation and deployment guides
- Performance optimization and caching

## Acknowledgments

- **MusicBrainz**: For providing the comprehensive music database
- **FastMCP**: For the excellent MCP framework
- **Model Context Protocol**: For the standardized protocol specification
- **Python Community**: For the amazing ecosystem of libraries

---

For more details about any release, see the [GitHub Releases](https://github.com/your-repo/releases) page.
