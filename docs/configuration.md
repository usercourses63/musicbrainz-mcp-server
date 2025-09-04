# Configuration Guide

This guide covers all configuration options for the MusicBrainz MCP Server.

## Configuration Methods

The server supports multiple configuration methods in order of precedence:

1. **Environment Variables** (highest priority)
2. **Configuration File** (`config.json`)
3. **Default Values** (lowest priority)

## Environment Variables

### MusicBrainz API Configuration

#### MUSICBRAINZ_USER_AGENT
- **Required**: Yes
- **Type**: String
- **Description**: User agent string for MusicBrainz API requests
- **Format**: `ApplicationName/Version (contact-info)`
- **Example**: `MyMusicApp/1.0.0 (user@example.com)`

```bash
export MUSICBRAINZ_USER_AGENT="MyMusicApp/1.0.0 (user@example.com)"
```

#### MUSICBRAINZ_RATE_LIMIT
- **Required**: No
- **Type**: Float
- **Default**: `1.0`
- **Description**: Maximum requests per second to MusicBrainz API
- **Range**: `0.1` to `10.0`
- **Recommendation**: Keep at `1.0` for public instances

```bash
export MUSICBRAINZ_RATE_LIMIT="1.0"
```

#### MUSICBRAINZ_TIMEOUT
- **Required**: No
- **Type**: Float
- **Default**: `10.0`
- **Description**: Request timeout in seconds
- **Range**: `1.0` to `60.0`

```bash
export MUSICBRAINZ_TIMEOUT="10.0"
```

### Caching Configuration

#### CACHE_ENABLED
- **Required**: No
- **Type**: Boolean
- **Default**: `true`
- **Description**: Enable/disable response caching

```bash
export CACHE_ENABLED="true"
```

#### CACHE_DEFAULT_TTL
- **Required**: No
- **Type**: Integer
- **Default**: `300`
- **Description**: Default cache TTL in seconds (5 minutes)
- **Range**: `60` to `3600`

```bash
export CACHE_DEFAULT_TTL="300"
```

#### CACHE_MAX_SIZE
- **Required**: No
- **Type**: Integer
- **Default**: `1000`
- **Description**: Maximum number of cached items

```bash
export CACHE_MAX_SIZE="1000"
```

### Server Configuration

#### DEBUG
- **Required**: No
- **Type**: Boolean
- **Default**: `false`
- **Description**: Enable debug logging

```bash
export DEBUG="true"
```

#### LOG_LEVEL
- **Required**: No
- **Type**: String
- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

```bash
export LOG_LEVEL="INFO"
```

#### SERVER_HOST
- **Required**: No
- **Type**: String
- **Default**: `localhost`
- **Description**: Server bind address

```bash
export SERVER_HOST="0.0.0.0"
```

#### SERVER_PORT
- **Required**: No
- **Type**: Integer
- **Default**: `8000`
- **Description**: Server port number

```bash
export SERVER_PORT="8000"
```

## Configuration File

Create a `config.json` file in the project root or specify the path with `CONFIG_FILE` environment variable.

### Basic Configuration

```json
{
  "api": {
    "user_agent": "MyMusicApp/1.0.0 (user@example.com)",
    "rate_limit": 1.0,
    "timeout": 10.0
  },
  "cache": {
    "enabled": true,
    "default_ttl": 300,
    "max_size": 1000
  },
  "server": {
    "host": "localhost",
    "port": 8000,
    "debug": false,
    "log_level": "INFO"
  }
}
```

### Production Configuration

```json
{
  "api": {
    "user_agent": "ProductionApp/2.1.0 (admin@company.com)",
    "rate_limit": 0.8,
    "timeout": 15.0
  },
  "cache": {
    "enabled": true,
    "default_ttl": 600,
    "max_size": 5000
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": false,
    "log_level": "WARNING"
  }
}
```

### Development Configuration

```json
{
  "api": {
    "user_agent": "DevApp/0.1.0 (dev@localhost)",
    "rate_limit": 2.0,
    "timeout": 5.0
  },
  "cache": {
    "enabled": false,
    "default_ttl": 60,
    "max_size": 100
  },
  "server": {
    "host": "localhost",
    "port": 8000,
    "debug": true,
    "log_level": "DEBUG"
  }
}
```

## Configuration Loading

### Custom Config File Path

```bash
export CONFIG_FILE="/path/to/custom/config.json"
```

### Configuration Validation

The server validates all configuration values on startup:

- **User Agent**: Must be non-empty string
- **Rate Limit**: Must be positive number
- **Timeout**: Must be positive number
- **TTL**: Must be positive integer
- **Port**: Must be valid port number (1-65535)

### Configuration Errors

Common configuration errors and solutions:

#### Missing User Agent
```
Error: MUSICBRAINZ_USER_AGENT is required
```
**Solution**: Set the environment variable or add to config file

#### Invalid Rate Limit
```
Error: Rate limit must be between 0.1 and 10.0
```
**Solution**: Adjust the rate limit value

#### Invalid Config File
```
Error: Invalid JSON in config file
```
**Solution**: Validate JSON syntax

## Environment-Specific Configurations

### Docker Environment

```dockerfile
ENV MUSICBRAINZ_USER_AGENT="DockerApp/1.0.0"
ENV MUSICBRAINZ_RATE_LIMIT="1.0"
ENV CACHE_ENABLED="true"
ENV DEBUG="false"
```

### Kubernetes Environment

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: musicbrainz-config
data:
  MUSICBRAINZ_USER_AGENT: "K8sApp/1.0.0"
  MUSICBRAINZ_RATE_LIMIT: "1.0"
  CACHE_ENABLED: "true"
  DEBUG: "false"
```

### Systemd Environment

```ini
[Service]
Environment=MUSICBRAINZ_USER_AGENT=SystemdApp/1.0.0
Environment=MUSICBRAINZ_RATE_LIMIT=1.0
Environment=CACHE_ENABLED=true
Environment=DEBUG=false
```

## Performance Tuning

### High-Traffic Configuration

For high-traffic scenarios:

```json
{
  "api": {
    "rate_limit": 0.5,
    "timeout": 20.0
  },
  "cache": {
    "enabled": true,
    "default_ttl": 1800,
    "max_size": 10000
  }
}
```

### Low-Latency Configuration

For low-latency requirements:

```json
{
  "api": {
    "rate_limit": 2.0,
    "timeout": 5.0
  },
  "cache": {
    "enabled": true,
    "default_ttl": 60,
    "max_size": 1000
  }
}
```

## Security Considerations

### Production Security

1. **Don't expose debug mode** in production
2. **Use appropriate log levels** to avoid sensitive data logging
3. **Bind to specific interfaces** instead of `0.0.0.0` when possible
4. **Use environment variables** for sensitive configuration
5. **Validate user agent** to prevent abuse

### Example Secure Configuration

```bash
# Use specific host binding
export SERVER_HOST="127.0.0.1"

# Disable debug mode
export DEBUG="false"

# Use warning level logging
export LOG_LEVEL="WARNING"

# Set conservative rate limit
export MUSICBRAINZ_RATE_LIMIT="0.8"
```

## Monitoring Configuration

### Health Check Endpoint

The server provides a health check endpoint at `/health` that returns:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "cache_stats": {
    "hits": 150,
    "misses": 50,
    "size": 200
  }
}
```

### Metrics Configuration

Enable metrics collection:

```json
{
  "metrics": {
    "enabled": true,
    "endpoint": "/metrics",
    "include_cache_stats": true
  }
}
```

## Troubleshooting Configuration

### Debug Configuration Issues

1. **Enable debug logging**:
```bash
export DEBUG="true"
export LOG_LEVEL="DEBUG"
```

2. **Check configuration loading**:
```bash
python -c "from musicbrainz_mcp.config import get_config; print(get_config())"
```

3. **Validate environment variables**:
```bash
env | grep MUSICBRAINZ
```

### Common Issues

#### Configuration Not Loading
- Check file permissions
- Verify JSON syntax
- Ensure environment variables are exported

#### Rate Limiting Too Aggressive
- Increase `MUSICBRAINZ_RATE_LIMIT`
- Enable caching to reduce API calls
- Implement request batching

#### Memory Usage High
- Reduce `CACHE_MAX_SIZE`
- Lower `CACHE_DEFAULT_TTL`
- Monitor cache hit rates

## Configuration Best Practices

1. **Use environment variables** for deployment-specific settings
2. **Keep config files** in version control (without secrets)
3. **Document custom configurations** for your deployment
4. **Test configuration changes** in staging first
5. **Monitor performance** after configuration changes
6. **Use conservative rate limits** to respect MusicBrainz API
7. **Enable caching** to improve performance and reduce API load
