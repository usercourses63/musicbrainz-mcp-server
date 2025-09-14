#!/bin/bash
# Test script for MCP protocol compliance using curl
# Tests the endpoints that Smithery.ai scanner expects

set -e

BASE_URL="http://localhost:8081"
FAILED=0

echo "🎵 MusicBrainz MCP Server - Curl-based Protocol Test"
echo "=================================================="

# Function to test an endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    local expected_status="$5"
    
    echo ""
    echo "🔧 Testing: $name"
    echo "   URL: $url"
    echo "   Method: $method"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$data" "$url")
    fi
    
    # Split response and status code
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    echo "   Status: $status_code"
    
    if [ "$status_code" = "$expected_status" ]; then
        echo "   ✅ PASS: Status code matches expected ($expected_status)"
        echo "   Response: $body" | head -c 200
        if [ ${#body} -gt 200 ]; then
            echo "..."
        fi
        echo ""
    else
        echo "   ❌ FAIL: Expected $expected_status, got $status_code"
        echo "   Response: $body"
        FAILED=1
    fi
}

# Test 1: Health check
test_endpoint "Health Check" "GET" "$BASE_URL/health" "" "200"

# Test 2: MCP Initialize
initialize_data='{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {}
    }
}'

test_endpoint "MCP Initialize" "POST" "$BASE_URL/mcp" "$initialize_data" "200"

# Test 3: MCP Tools List
tools_data='{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
}'

test_endpoint "MCP Tools List" "POST" "$BASE_URL/mcp" "$tools_data" "200"

# Test 4: Tools endpoint (legacy)
test_endpoint "Tools Endpoint" "GET" "$BASE_URL/tools" "" "200"

# Test 5: Test endpoint
test_endpoint "Test Endpoint" "GET" "$BASE_URL/test" "" "200"

# Test 6: Invalid JSON to MCP endpoint
invalid_data='{"invalid": "json"'

echo ""
echo "🔧 Testing: Invalid JSON Handling"
echo "   URL: $BASE_URL/mcp"
echo "   Method: POST"

response=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -d "$invalid_data" "$BASE_URL/mcp")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n -1)

echo "   Status: $status_code"

if [ "$status_code" = "400" ]; then
    echo "   ✅ PASS: Invalid JSON properly rejected with 400"
else
    echo "   ❌ FAIL: Expected 400 for invalid JSON, got $status_code"
    FAILED=1
fi

# Summary
echo ""
echo "=================================================="
echo "📊 Test Summary"
echo "=================================================="

if [ $FAILED -eq 0 ]; then
    echo "🎉 All curl tests passed! Server is ready for Smithery.ai deployment."
    echo ""
    echo "Next steps:"
    echo "1. Build and run Docker container: docker build -t musicbrainz-mcp . && docker run -p 8081:8081 musicbrainz-mcp"
    echo "2. Run this test script against the container"
    echo "3. Deploy to Smithery.ai"
    exit 0
else
    echo "⚠️ Some tests failed. Please fix issues before deployment."
    exit 1
fi
