"""
LinkedIn URL Extraction Module

Extracts LinkedIn profile URLs from GitHub user profiles using multiple strategies:
1. Extract from bio/description
2. Extract from blog/website field
3. Extract from social accounts (GitHub API)
4. Guess from GitHub username with verification
"""

import re
import requests
import time
from typing import Optional

def extract_linkedin_from_text(text: str) -> Optional[str]:
    """
    Extract LinkedIn URL from any text (bio, blog, etc.)
    
    Handles formats:
    - https://linkedin.com/in/username
    - https://www.linkedin.com/in/username
    - linkedin.com/in/username
    - linkedin.com/in/username/
    """
    if not text:
        return None
    
    # Pattern to match LinkedIn profile URLs
    patterns = [
        r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)',
        r'linkedin\.com/in/([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            username = match.group(1).rstrip('/')
            return f"https://www.linkedin.com/in/{username}"
    
    return None

def verify_linkedin_url(url: str, timeout: int = 5) -> bool:
    """
    Verify that a LinkedIn URL exists by making a HEAD request.
    
    Returns True if the URL returns 200 OK, False otherwise.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except:
        return False


def extract_linkedin_from_github_user(user, verify_guesses: bool = False, use_google_fallback: bool = False) -> Optional[str]:
    """
    Extract LinkedIn URL from a GitHub user object (PyGithub User).
    
    HYBRID APPROACH:
    1. Try GitHub profile data first (bio, blog, social accounts)
    2. If not found and use_google_fallback=True, try Google Custom Search
    
    Args:
        user: PyGithub User object
        verify_guesses: Ignored (kept for compatibility)
        use_google_fallback: If True, use Google Custom Search as fallback
    
    Returns:
        LinkedIn URL string or None (only verified URLs)
    """
    linkedin_url = None
    
    # Strategy 1: Check bio
    if user.bio:
        linkedin_url = extract_linkedin_from_text(user.bio)
        if linkedin_url:
            return linkedin_url
    
    # Strategy 2: Check blog/website field
    if user.blog:
        linkedin_url = extract_linkedin_from_text(user.blog)
        if linkedin_url:
            return linkedin_url
    
    # Strategy 3: Check social accounts (newer GitHub API feature)
    try:
        social_accounts = user.get_social_accounts()
        for account in social_accounts:
            if hasattr(account, 'provider') and 'linkedin' in account.provider.lower():
                return account.url
            if hasattr(account, 'url') and 'linkedin.com' in account.url:
                linkedin_url = extract_linkedin_from_text(account.url)
                if linkedin_url:
                    return linkedin_url
    except:
        # Social accounts API might not be available or might fail
        pass
    
    # Strategy 4: Google Custom Search fallback (if enabled)
    if use_google_fallback and not linkedin_url:
        try:
            from google_linkedin_finder import find_linkedin_via_google
            name = user.name
            location = user.location
            github_username = user.login
            
            linkedin_url = find_linkedin_via_google(name, location, github_username)
            if linkedin_url:
                return linkedin_url
        except ImportError:
            # Google API not set up yet
            pass
        except Exception as e:
            # Google API error - continue without it
            pass
    
    return None

def batch_extract_linkedin_urls(github_client, usernames: list, verify_guesses: bool = False, delay: float = 0.5) -> dict:
    """
    Extract LinkedIn URLs for a batch of GitHub usernames.
    
    Args:
        github_client: PyGithub Github object
        usernames: List of GitHub usernames
        verify_guesses: If True, verify guessed URLs (slower)
        delay: Delay between requests to avoid rate limiting
    
    Returns:
        Dictionary mapping username -> LinkedIn URL (or None)
    """
    results = {}
    
    for i, username in enumerate(usernames):
        try:
            user = github_client.get_user(username)
            linkedin_url = extract_linkedin_from_github_user(user, verify_guesses=verify_guesses)
            results[username] = linkedin_url
            
            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{len(usernames)} users for LinkedIn extraction")
            
            time.sleep(delay)
        except Exception as e:
            print(f"Error extracting LinkedIn for {username}: {e}")
            results[username] = None
    
    return results

# Test function
if __name__ == "__main__":
    # Test extraction from text
    test_bio = "Software Engineer | https://linkedin.com/in/johndoe | Open source enthusiast"
    print("Test bio:", test_bio)
    print("Extracted:", extract_linkedin_from_text(test_bio))
    
    # Test URL verification
    test_url = "https://www.linkedin.com/in/satyanadella"  # Microsoft CEO
    print(f"\nVerifying {test_url}...")
    print("Exists:", verify_linkedin_url(test_url))
