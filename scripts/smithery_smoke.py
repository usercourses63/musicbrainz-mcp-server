import asyncio, json
import httpx
from musicbrainz_mcp.server import create_http_app_for_tests

async def main():
    app = create_http_app_for_tests()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Health
        r1 = await client.get("/health")
        print("HEALTH:", r1.status_code)
        print(r1.json())

        # Provide Smithery-style flat query params
        ua = "TestApp/1.0 (test@example.com)"
        params = {"user_agent": ua, "rate_limit": "1.0", "timeout": "30"}

        r2 = await client.get("/test", params=params)
        print("TEST:", r2.status_code)
        print(r2.json())

        r3 = await client.get("/tools", params=params)
        print("TOOLS:", r3.status_code)
        data = r3.json()
        print({"status": data.get("status"), "tool_count": len(data.get("tools", []))})

if __name__ == "__main__":
    asyncio.run(main())

