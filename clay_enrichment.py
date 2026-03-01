"""
Clay.com API Integration for LinkedIn Profile Enrichment

Uses Clay.com's HTTP API to enrich candidates with LinkedIn URLs.

Requirements:
- Clay.com account with API access
- CLAY_API_KEY in .env file

Documentation:
- Clay HTTP API: https://university.clay.com/docs/http-api-integration-overview
- Clay Webhooks: https://university.clay.com/docs/webhook-integration-guide
"""

import os
import requests
import time
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()

CLAY_API_KEY = os.getenv("CLAY_API_KEY")

class ClayEnrichmentClient:
    """
    Client for enriching candidate data using Clay.com API.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or CLAY_API_KEY
        if not self.api_key:
            raise ValueError("CLAY_API_KEY not found in environment variables")
        
        self.base_url = "https://api.clay.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def test_connection(self) -> bool:
        """
        Test if API key is valid and connection works.
        """
        try:
            # Try to access API (exact endpoint depends on Clay's API structure)
            response = requests.get(
                f"{self.base_url}/me",  # Common endpoint for API validation
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Clay API connection successful")
                return True
            elif response.status_code == 401:
                print("❌ Clay API key is invalid")
                return False
            else:
                print(f"⚠️ Clay API returned status {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error connecting to Clay API: {e}")
            return False
    
    def enrich_linkedin_url(
        self, 
        name: str, 
        location: str = None, 
        company: str = None,
        github_username: str = None
    ) -> Optional[str]:
        """
        Find LinkedIn URL for a person using Clay enrichment.
        
        Args:
            name: Full name of the person
            location: Location (city, state, country)
            company: Company name
            github_username: GitHub username (for reference)
        
        Returns:
            LinkedIn URL or None if not found
        """
        # Note: The exact API endpoint and structure depends on Clay's API
        # This is a template that will need to be adjusted based on Clay's actual API
        
        try:
            payload = {
                "name": name,
                "location": location,
                "company": company,
                "github_username": github_username
            }
            
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}
            
            # This endpoint is hypothetical - needs to be updated with actual Clay API
            response = requests.post(
                f"{self.base_url}/enrich/linkedin",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                linkedin_url = data.get('linkedin_url')
                return linkedin_url
            else:
                print(f"Clay API error for {name}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error enriching {name}: {e}")
            return None
    
    def batch_enrich_linkedin(
        self, 
        candidates: List[Dict],
        delay: float = 1.0
    ) -> Dict[str, Optional[str]]:
        """
        Batch enrich multiple candidates with LinkedIn URLs.
        
        Args:
            candidates: List of dicts with 'name', 'location', 'company', 'github_username'
            delay: Delay between requests to avoid rate limiting
        
        Returns:
            Dictionary mapping github_username -> LinkedIn URL
        """
        results = {}
        
        for i, candidate in enumerate(candidates):
            name = candidate.get('name')
            location = candidate.get('location')
            company = candidate.get('company')
            github_username = candidate.get('github_username')
            
            if not name or not github_username:
                continue
            
            linkedin_url = self.enrich_linkedin_url(
                name=name,
                location=location,
                company=company,
                github_username=github_username
            )
            
            results[github_username] = linkedin_url
            
            if (i + 1) % 10 == 0:
                print(f"Enriched {i + 1}/{len(candidates)} candidates")
            
            time.sleep(delay)
        
        return results


# Test function
if __name__ == "__main__":
    print("Testing Clay.com API Integration...")
    print("=" * 80)
    
    if not CLAY_API_KEY:
        print("\n❌ ERROR: CLAY_API_KEY not found in .env file")
        print("\nPlease add to .env:")
        print("CLAY_API_KEY=your_api_key_here")
    else:
        print(f"\n✅ API Key found: {CLAY_API_KEY[:10]}...")
        
        # Test connection
        client = ClayEnrichmentClient()
        client.test_connection()
        
        print("\n" + "=" * 80)
        print("NOTE: Clay.com API structure may vary by plan.")
        print("Starter plan may have limited API access.")
        print("You may need to use Clay's webhook/table approach instead.")
        print("=" * 80)
