"""
Test the Custom Search Engine configuration to diagnose the issue.
"""

import os
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

print("Testing CSE Configuration...")
print("=" * 80)
print(f"API Key: {GOOGLE_API_KEY[:20]}... (truncated)")
print(f"CSE ID: {GOOGLE_CSE_ID}")
print()

# Try a simple search without site restriction first
service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)

print("Test 1: Simple search (no site restriction)")
print("-" * 80)
try:
    result = service.cse().list(
        q="test",
        cx=GOOGLE_CSE_ID,
        num=1
    ).execute()
    print("✅ SUCCESS - CSE is working!")
    print(f"Found {result.get('searchInformation', {}).get('totalResults', 0)} results")
except Exception as e:
    print(f"❌ FAILED: {e}")

print()
print("Test 2: Search with site restriction")
print("-" * 80)
try:
    result = service.cse().list(
        q="test site:linkedin.com",
        cx=GOOGLE_CSE_ID,
        num=1
    ).execute()
    print("✅ SUCCESS - Site restriction works!")
    print(f"Found {result.get('searchInformation', {}).get('totalResults', 0)} results")
except Exception as e:
    print(f"❌ FAILED: {e}")

print()
print("Test 3: LinkedIn profile search")
print("-" * 80)
try:
    result = service.cse().list(
        q="Michael Merrill",
        cx=GOOGLE_CSE_ID,
        num=1
    ).execute()
    print("✅ SUCCESS - LinkedIn search works!")
    if 'items' in result:
        print(f"First result: {result['items'][0].get('link', 'N/A')}")
    else:
        print("No results found")
except Exception as e:
    print(f"❌ FAILED: {e}")
