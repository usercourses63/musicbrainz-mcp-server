#!/usr/bin/env python3
"""
Test script to validate MCP protocol compliance for Smithery.ai deployment.

This script tests the MCP initialization endpoints that Smithery.ai scanner expects:
1. MCP initialize request
2. MCP tools/list request
3. Validates JSON-RPC 2.0 compliance
"""

import asyncio
import json
import sys
from typing import Dict, Any

import httpx


async def test_mcp_initialize(client: httpx.AsyncClient, base_url: str) -> bool:
    """Test MCP initialize request."""
    print("🔧 Testing MCP initialize request...")
    
    initialize_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {}
        }
    }
    
    try:
        response = await client.post(
            f"{base_url}/mcp",
            json=initialize_request,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ FAIL: Expected 200, got {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)}")
        
        # Validate JSON-RPC 2.0 response
        if data.get("jsonrpc") != "2.0":
            print("   ❌ FAIL: Missing or invalid jsonrpc field")
            return False
        
        if "result" not in data:
            print("   ❌ FAIL: Missing result field")
            return False
        
        result = data["result"]
        if result.get("protocolVersion") != "2024-11-05":
            print("   ❌ FAIL: Invalid protocol version")
            return False
        
        if "capabilities" not in result:
            print("   ❌ FAIL: Missing capabilities")
            return False
        
        if "serverInfo" not in result:
            print("   ❌ FAIL: Missing serverInfo")
            return False
        
        server_info = result["serverInfo"]
        if server_info.get("name") != "MusicBrainz MCP Server":
            print("   ❌ FAIL: Invalid server name")
            return False
        
        print("   ✅ PASS: MCP initialize request successful")
        return True
        
    except Exception as e:
        print(f"   ❌ FAIL: Exception during initialize test: {e}")
        return False


async def test_mcp_tools_list(client: httpx.AsyncClient, base_url: str) -> bool:
    """Test MCP tools/list request."""
    print("🔧 Testing MCP tools/list request...")
    
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        response = await client.post(
            f"{base_url}/mcp",
            json=tools_request,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ FAIL: Expected 200, got {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        data = response.json()
        
        # Validate JSON-RPC 2.0 response
        if data.get("jsonrpc") != "2.0":
            print("   ❌ FAIL: Missing or invalid jsonrpc field")
            return False
        
        if "result" not in data:
            print("   ❌ FAIL: Missing result field")
            return False
        
        result = data["result"]
        if "tools" not in result:
            print("   ❌ FAIL: Missing tools field")
            return False
        
        tools = result["tools"]
        if not isinstance(tools, list):
            print("   ❌ FAIL: Tools field is not a list")
            return False
        
        if len(tools) == 0:
            print("   ❌ FAIL: No tools found")
            return False
        
        print(f"   Found {len(tools)} tools:")
        for tool in tools:
            if "name" not in tool or "description" not in tool or "inputSchema" not in tool:
                print(f"   ❌ FAIL: Invalid tool structure: {tool}")
                return False
            print(f"     - {tool['name']}: {tool['description']}")
        
        print("   ✅ PASS: MCP tools/list request successful")
        return True
        
    except Exception as e:
        print(f"   ❌ FAIL: Exception during tools/list test: {e}")
        return False


async def test_health_endpoint(client: httpx.AsyncClient, base_url: str) -> bool:
    """Test health endpoint."""
    print("🔧 Testing health endpoint...")
    
    try:
        response = await client.get(f"{base_url}/health")
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ FAIL: Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        if data.get("status") != "healthy":
            print(f"   ❌ FAIL: Server not healthy: {data}")
            return False
        
        print("   ✅ PASS: Health endpoint successful")
        return True
        
    except Exception as e:
        print(f"   ❌ FAIL: Exception during health test: {e}")
        return False


async def test_invalid_mcp_request(client: httpx.AsyncClient, base_url: str) -> bool:
    """Test invalid MCP request handling."""
    print("🔧 Testing invalid MCP request handling...")
    
    invalid_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "invalid_method",
        "params": {}
    }
    
    try:
        response = await client.post(
            f"{base_url}/mcp",
            json=invalid_request,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        
        # Should either return None (delegated to FastMCP) or handle gracefully
        # We don't expect a 500 error for unknown methods
        if response.status_code >= 500:
            print(f"   ❌ FAIL: Server error for unknown method: {response.status_code}")
            return False
        
        print("   ✅ PASS: Invalid request handled gracefully")
        return True
        
    except Exception as e:
        print(f"   ❌ FAIL: Exception during invalid request test: {e}")
        return False


async def main():
    """Run all MCP protocol compliance tests."""
    print("🎵 MusicBrainz MCP Server - Smithery.ai Protocol Compliance Test")
    print("=" * 60)
    
    # Test against local server
    base_url = "http://localhost:9000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        tests = [
            ("Health Check", test_health_endpoint),
            ("MCP Initialize", test_mcp_initialize),
            ("MCP Tools List", test_mcp_tools_list),
            ("Invalid Request Handling", test_invalid_mcp_request),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                result = await test_func(client, base_url)
                results.append((test_name, result))
            except Exception as e:
                print(f"   ❌ FAIL: Unexpected error: {e}")
                results.append((test_name, False))
        
        print("\n" + "=" * 60)
        print("📊 Test Results Summary:")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
            if result:
                passed += 1
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Server is ready for Smithery.ai deployment.")
            return 0
        else:
            print("⚠️ Some tests failed. Please fix issues before deployment.")
            return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
