# Smithery.ai MCP Protocol Testing Guide

This guide provides comprehensive testing instructions to validate that the MusicBrainz MCP Server is ready for Smithery.ai deployment.

## Quick Test Commands

### 1. Start the Server Locally

```bash
# Build and run Docker container
docker build -t musicbrainz-mcp .
docker run -p 8081:8081 musicbrainz-mcp
```

### 2. Test MCP Protocol Endpoints

#### Health Check
```bash
curl http://localhost:8081/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "MusicBrainz MCP Server",
  "version": "1.1.0",
  "tools_count": 10,
  "ready": true
}
```

#### MCP Initialize Request
```bash
curl -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {}
    }
  }'
```

Expected response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {
        "listChanged": false
      }
    },
    "serverInfo": {
      "name": "MusicBrainz MCP Server",
      "version": "1.1.0"
    }
  }
}
```

#### MCP Tools List Request
```bash
curl -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'
```

Expected response: JSON with 10 tools including `search_artist`, `search_release`, etc.

### 3. Run Automated Tests

#### Python Test Script
```bash
python scripts/test_smithery_mcp_protocol.py
```

#### PowerShell Test (Windows)
```powershell
# Test health endpoint
Invoke-RestMethod -Uri "http://localhost:8081/health" -Method GET

# Test MCP initialize
$initBody = @{
    jsonrpc = "2.0"
    id = 1
    method = "initialize"
    params = @{
        protocolVersion = "2024-11-05"
        capabilities = @{}
    }
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri "http://localhost:8081/mcp" -Method POST -Body $initBody -ContentType "application/json"

# Test tools list
$toolsBody = @{
    jsonrpc = "2.0"
    id = 2
    method = "tools/list"
    params = @{}
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8081/mcp" -Method POST -Body $toolsBody -ContentType "application/json"
```

## Key Validation Points

### ✅ MCP Protocol Compliance
- [x] JSON-RPC 2.0 format
- [x] Proper `initialize` method handling
- [x] Proper `tools/list` method handling
- [x] Correct protocol version (2024-11-05)
- [x] Server capabilities declaration

### ✅ Smithery.ai Requirements
- [x] HTTP transport on port 8081
- [x] CORS headers for browser compatibility
- [x] Configuration schema in smithery.yaml
- [x] Optional configuration fields for scanning
- [x] Default configuration for tool discovery

### ✅ Error Handling
- [x] Invalid JSON returns 400 with proper error
- [x] Unknown methods handled gracefully
- [x] Server errors return proper JSON-RPC error format

### ✅ Tool Discovery
- [x] 10 tools available for discovery
- [x] Proper tool schema with inputSchema
- [x] Tools work without user configuration

## Troubleshooting

### Common Issues

1. **Port 8081 not accessible**
   - Check if Docker container is running: `docker ps`
   - Check port mapping: `docker run -p 8081:8081 musicbrainz-mcp`

2. **MCP endpoints return 404**
   - Verify the `/mcp` route is registered
   - Check server logs for initialization errors

3. **Tools list empty**
   - Check MusicBrainz client initialization
   - Verify default configuration is applied

4. **JSON-RPC format errors**
   - Ensure Content-Type is `application/json`
   - Validate JSON structure with online validator

### Expected Log Output

When server starts successfully, you should see:
```
🎵 Starting MusicBrainz MCP Server v1.1.0...
🔧 Environment check:
   PORT: 8081
🌐 Starting HTTP server on port 8081
✅ Dependencies validated: FastMCP X.X.X
🔧 Creating FastMCP HTTP app...
✅ FastMCP HTTP app created successfully
🔧 Initializing MusicBrainz client with default configuration...
✅ MusicBrainz client configured successfully for scanning
🚀 Server configured for port 8081, starting...
🔍 Health check will be available at /health
🔧 MCP endpoint will be available at /mcp
```

When MCP requests are received:
```
🔧 Handling MCP initialize request from Smithery.ai scanner
✅ MCP initialize response sent successfully
🔧 Handling MCP tools/list request from Smithery.ai scanner
✅ MCP tools/list response sent successfully with 10 tools
```

## Deployment Readiness Checklist

- [ ] All automated tests pass
- [ ] Docker container builds successfully
- [ ] Health endpoint returns 200
- [ ] MCP initialize returns proper JSON-RPC response
- [ ] MCP tools/list returns 10 tools
- [ ] Server handles invalid requests gracefully
- [ ] Configuration is optional for scanning
- [ ] Default user agent is Smithery-compatible

Once all items are checked, the server is ready for Smithery.ai deployment!
