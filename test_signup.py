"""Test the signup endpoint."""
import httpx
import json

async def test_signup():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/auth/signup",
            json={
                "email": "testuser@example.com",
                "password": "Test@123456",
                "first_name": "Test",
                "last_name": "User"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 201

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(test_signup())
    print(f"\nSignup test: {'PASSED' if result else 'FAILED'}")
