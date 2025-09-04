#!/usr/bin/env python3
"""
Test script to verify MusicBrainz MCP Server starts correctly
This simulates the smithery.ai deployment environment
"""
import asyncio
import os
import signal
import subprocess
import sys
import time
import httpx

async def test_server_startup():
    """Test that the server starts and responds to health checks"""
    
    print("🧪 Testing MusicBrainz MCP Server startup...")
    
    # Set environment variables for testing
    env = os.environ.copy()
    env["PORT"] = "8081"
    env["MUSICBRAINZ_USER_AGENT"] = "TestServer/1.0.0 (test@example.com)"
    env["PYTHONUNBUFFERED"] = "1"
    
    # Start the server process
    print("🚀 Starting server process...")
    process = subprocess.Popen(
        [sys.executable, "-m", "musicbrainz_mcp.server"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        await asyncio.sleep(5)
        
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print("❌ Server process exited early!")
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            return False
        
        print("✅ Server process is running")
        
        # Test health endpoint
        print("🏥 Testing health endpoint...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://localhost:8081/health", timeout=10)
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"✅ Health check passed: {health_data}")
                else:
                    print(f"❌ Health check failed: {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ Health check error: {e}")
                return False
        
        # Test MCP endpoint
        print("🔧 Testing MCP endpoint...")
        try:
            response = await client.get("http://localhost:8081/mcp", timeout=10)
            print(f"✅ MCP endpoint accessible: {response.status_code}")
        except Exception as e:
            print(f"⚠️ MCP endpoint test: {e}")
        
        # Let server run for a bit to ensure it doesn't exit
        print("⏳ Testing server stability (10 seconds)...")
        await asyncio.sleep(10)
        
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print("❌ Server exited during stability test!")
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            return False
        
        print("✅ Server stability test passed")
        
        # Final health check
        print("🏥 Final health check...")
        try:
            response = await client.get("http://localhost:8081/health", timeout=5)
            if response.status_code == 200:
                print("✅ Final health check passed")
                return True
            else:
                print(f"❌ Final health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Final health check error: {e}")
            return False
            
    finally:
        # Clean up
        print("🧹 Cleaning up...")
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        print("✅ Cleanup complete")

async def main():
    """Main test function"""
    try:
        success = await test_server_startup()
        if success:
            print("\n🎉 SUCCESS: Server startup test passed!")
            print("✅ Server starts correctly")
            print("✅ Health endpoint responds")
            print("✅ Server remains stable")
            print("🚀 Ready for smithery.ai deployment!")
            sys.exit(0)
        else:
            print("\n❌ FAILURE: Server startup test failed!")
            print("🔧 Server needs fixes before deployment")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 TEST ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
