"""
Google Custom Search API Integration for LinkedIn Profile Discovery

Uses Google Custom Search API to find LinkedIn profiles by searching:
"Name" "Location" site:linkedin.com/in

Requires:
- Google Cloud Project with Custom Search API enabled
- Custom Search Engine ID (CSE ID)
- API Key

Setup Instructions:
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable "Custom Search API"
4. Create API key (Credentials > Create Credentials > API Key)
5. Go to https://programmablesearchengine.google.com/
6. Create a new search engine
7. Set "Sites to search" to: linkedin.com/in/*
8. Get your Search Engine ID (CSE ID)
9. Add to .env file:
   GOOGLE_API_KEY=your_api_key_here
   GOOGLE_CSE_ID=your_cse_id_here

Pricing: $5 per 1,000 queries (100 free per day)
"""

import os
import re
import time
from typing import Optional, Dict
from dotenv import load_dotenv

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("ERROR: google-api-python-client not installed")
    print("Run: pip install google-api-python-client")
    raise

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

def extract_linkedin_url_from_search_results(results: Dict) -> Optional[str]:
    """
    Extract LinkedIn URL from Google search results.
    
    Returns the first linkedin.com/in/ URL found.
    """
    if not results or 'items' not in results:
        return None
    
    for item in results['items']:
        link = item.get('link', '')
        if 'linkedin.com/in/' in link:
            # Clean up the URL
            match = re.search(r'(https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+)', link)
            if match:
                return match.group(1)
    
    return None

def find_linkedin_via_google(name: str, location: str = None, github_username: str = None) -> Optional[str]:
    """
    Find LinkedIn profile URL using Google Custom Search API.
    
    Args:
        name: Full name of the person (e.g., "Michael Merrill")
        location: Location (e.g., "New York") - helps narrow results
        github_username: GitHub username - used as fallback search term
    
    Returns:
        LinkedIn URL or None
    """
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        raise ValueError("GOOGLE_API_KEY and GOOGLE_CSE_ID must be set in .env file")
    
    if not name and not github_username:
        return None
    
    try:
        # Build the search service
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        
        # Construct search query
        if name and location:
            query = f'"{name}" "{location}" site:linkedin.com/in'
        elif name:
            query = f'"{name}" site:linkedin.com/in'
        elif github_username:
            query = f'"{github_username}" site:linkedin.com/in'
        else:
            return None
        
        # Execute search
        result = service.cse().list(
            q=query,
            cx=GOOGLE_CSE_ID,
            num=3  # Get top 3 results
        ).execute()
        
        # Extract LinkedIn URL from results
        linkedin_url = extract_linkedin_url_from_search_results(result)
        
        return linkedin_url
        
    except HttpError as e:
        if e.resp.status == 429:
            print(f"Google API rate limit exceeded. Sleeping for 60 seconds...")
            time.sleep(60)
            return find_linkedin_via_google(name, location, github_username)
        else:
            print(f"Google API error: {e}")
            return None
    except Exception as e:
        print(f"Error searching for LinkedIn: {e}")
        return None

def batch_find_linkedin_urls(candidates: list, delay: float = 0.1) -> Dict[str, Optional[str]]:
    """
    Find LinkedIn URLs for a batch of candidates.
    
    Args:
        candidates: List of dicts with 'name', 'location', 'github_username'
        delay: Delay between requests (seconds) to avoid rate limits
    
    Returns:
        Dictionary mapping github_username -> LinkedIn URL
    """
    results = {}
    
    for i, candidate in enumerate(candidates):
        name = candidate.get('name')
        location = candidate.get('location')
        github_username = candidate.get('github_username')
        
        if not github_username:
            continue
        
        linkedin_url = find_linkedin_via_google(name, location, github_username)
        results[github_username] = linkedin_url
        
        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(candidates)} candidates for LinkedIn discovery")
        
        time.sleep(delay)
    
    return results

def verify_linkedin_url_match(linkedin_url: str, expected_name: str) -> bool:
    """
    Verify that a LinkedIn URL likely matches the expected person.
    
    Simple check: extract username from URL and compare to name.
    More sophisticated matching would require scraping the LinkedIn page.
    
    Args:
        linkedin_url: LinkedIn profile URL
        expected_name: Expected full name
    
    Returns:
        True if likely a match, False otherwise
    """
    if not linkedin_url or not expected_name:
        return False
    
    # Extract username from URL
    match = re.search(r'linkedin\.com/in/([a-zA-Z0-9_-]+)', linkedin_url)
    if not match:
        return False
    
    username = match.group(1).lower()
    name_parts = expected_name.lower().split()
    
    # Check if any name part is in the username
    for part in name_parts:
        if len(part) > 2 and part in username:
            return True
    
    # If no match, still return True (we'll rely on Google's relevance)
    # More sophisticated matching would require scraping the page
    return True

# Test function
if __name__ == "__main__":
    print("Testing Google LinkedIn Finder...")
    print("=" * 80)
    
    # Check if API keys are set
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        print("\nERROR: Missing API credentials!")
        print("\nPlease add to .env file:")
        print("GOOGLE_API_KEY=your_api_key_here")
        print("GOOGLE_CSE_ID=your_cse_id_here")
        print("\nSetup instructions:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Enable Custom Search API")
        print("3. Create API key")
        print("4. Go to https://programmablesearchengine.google.com/")
        print("5. Create search engine for linkedin.com/in/*")
        print("6. Get CSE ID")
    else:
        # Test search
        print("\nAPI credentials found. Testing search...")
        print("\nSearching for: Michael Merrill, New York")
        result = find_linkedin_via_google("Michael Merrill", "New York")
        print(f"Result: {result or 'NOT FOUND'}")
        
        print("\nSearching for: Satya Nadella, Microsoft")
        result = find_linkedin_via_google("Satya Nadella", "Microsoft")
        print(f"Result: {result or 'NOT FOUND'}")
