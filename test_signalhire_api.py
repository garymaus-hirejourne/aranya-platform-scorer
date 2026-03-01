import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SIGNALHIRE_API_KEY")
print(f"API Key loaded: {API_KEY[:20]}..." if API_KEY else "API Key: NOT FOUND")

# Test different endpoints and authentication methods
tests = [
    {
        "name": "Test 1: /api/v1/person with apikey header",
        "url": "https://www.signalhire.com/api/v1/person",
        "headers": {"Content-Type": "application/json", "apikey": API_KEY},
        "payload": {"items": ["https://www.linkedin.com/in/test"], "callbackUrl": "https://test.com/callback"}
    },
    {
        "name": "Test 2: /api/v1/person with Authorization Bearer",
        "url": "https://www.signalhire.com/api/v1/person",
        "headers": {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
        "payload": {"items": ["https://www.linkedin.com/in/test"], "callbackUrl": "https://test.com/callback"}
    },
    {
        "name": "Test 3: /api/v1/person with x-api-key header",
        "url": "https://www.signalhire.com/api/v1/person",
        "headers": {"Content-Type": "application/json", "x-api-key": API_KEY},
        "payload": {"items": ["https://www.linkedin.com/in/test"], "callbackUrl": "https://test.com/callback"}
    },
    {
        "name": "Test 4: /api/v1/candidate/search with apikey header",
        "url": "https://www.signalhire.com/api/v1/candidate/search",
        "headers": {"Content-Type": "application/json", "apikey": API_KEY},
        "payload": {"items": ["https://www.linkedin.com/in/test"], "callbackUrl": "https://test.com/callback"}
    }
]

for test in tests:
    print(f"\n{'='*60}")
    print(test["name"])
    print(f"{'='*60}")
    try:
        resp = requests.post(
            test["url"],
            headers=test["headers"],
            json=test["payload"],
            timeout=10
        )
        print(f"Status Code: {resp.status_code}")
        print(f"Headers: {dict(resp.headers)}")
        print(f"Response (first 500 chars):\n{resp.text[:500]}")
        
        # Try to parse as JSON
        try:
            json_data = resp.json()
            print(f"JSON Response: {json_data}")
        except:
            print("Response is not JSON (likely HTML)")
            
    except Exception as e:
        print(f"Error: {e}")

print(f"\n{'='*60}")
print("Testing complete")
