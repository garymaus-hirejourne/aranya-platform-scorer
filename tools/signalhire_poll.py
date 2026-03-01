"""
Poll SignalHire API for enrichment results instead of waiting for webhooks.
This is a fallback for when Ngrok free tier blocks webhook delivery.
"""

import requests
import os
import sys
import json
import time
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

API_KEY = os.getenv("SIGNALHIRE_API_KEY", "YOUR_SIGNALHIRE_KEY")
ENDPOINT = "https://www.signalhire.com/api/v1/candidate/search"

def poll_request(request_id, max_attempts=30, delay_seconds=10):
    """
    Poll SignalHire for results of a specific request ID.
    
    Args:
        request_id: The request ID returned from the initial API call
        max_attempts: Maximum number of polling attempts
        delay_seconds: Seconds to wait between attempts
    
    Returns:
        dict: The enrichment results or None if timeout
    """
    print(f"Polling for request ID: {request_id}")
    
    # SignalHire doesn't have a documented polling endpoint, so we'll need to
    # check their API documentation or contact support for the correct endpoint
    # For now, this is a placeholder that shows the pattern
    
    poll_url = f"https://www.signalhire.com/api/v1/request/{request_id}"
    
    for attempt in range(max_attempts):
        try:
            resp = requests.get(
                poll_url,
                headers={"apikey": API_KEY},
                timeout=10
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "completed":
                    print(f"Results ready after {attempt + 1} attempts")
                    return data
                elif data.get("status") == "failed":
                    print(f"Request failed: {data.get('error', 'Unknown error')}")
                    return None
                else:
                    print(f"Attempt {attempt + 1}/{max_attempts}: Status = {data.get('status', 'unknown')}")
            elif resp.status_code == 404:
                print(f"Request ID not found: {request_id}")
                return None
            else:
                print(f"Attempt {attempt + 1}/{max_attempts}: HTTP {resp.status_code}")
                
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_attempts}: Error - {e}")
        
        if attempt < max_attempts - 1:
            time.sleep(delay_seconds)
    
    print(f"Timeout after {max_attempts} attempts")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/signalhire_poll.py <request_id>")
        sys.exit(1)
    
    request_id = sys.argv[1]
    results = poll_request(request_id)
    
    if results:
        print(json.dumps(results, indent=2))
    else:
        print("No results available")
        sys.exit(1)
