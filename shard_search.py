import os
import requests
import datetime
import time
import csv
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN") # Using the name from your .env
if not TOKEN:
    raise ValueError("MISSING TOKEN: Set the GITHUB_TOKEN environment variable in .env.")

HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}

# 50 States for Geographic Sharding (Gemini Strategy)
STATES = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", 
          "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", 
          "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", 
          "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", 
          "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", 
          "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", 
          "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", 
          "Wisconsin", "Wyoming"]

def log_to_tasks(message):
    path = Path("tasks/todo.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"- [{timestamp}] {message}\n")

def run_deep_search():
    total_found = 0
    all_extracted_users = []
    
    log_to_tasks("STARTING DEEP SEARCH: 50 States x 10 Years.")
    print("Starting Deep Search (50 States + 'Platform Engineer')...")
    
    for state in STATES:
        state_found = 0
        print(f"\n--- Scanning State: {state} ---")
        
        for year in range(2015, 2026):
            # The "Backdoor" query format: State + Go + Terraform + Year
            query = f'location:"{state}" language:go language:hcl created:{year}-01-01..{year}-12-31'
            
            page = 1
            year_users = []
            
            while True:
                url = f"https://api.github.com/search/users?q={query}&per_page=100&page={page}"
                
                try:
                    response = requests.get(url, headers=HEADERS, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        count = data.get('total_count', 0)
                        items = data.get('items', [])
                        
                        if page == 1:
                            print(f"  {year}: Found {count} users.")
                            if count > 1000:
                                log_to_tasks(f"WARNING: {state} {year} exceeded 1000 limit ({count}).")
                        
                        if not items:
                            break # No more pages
                            
                        for item in items:
                            year_users.append({
                                "username": item['login'],
                                "shard_date": f"{state} {year}",
                                "html_url": item['html_url']
                            })
                            
                        # Pagination logic
                        if page >= 10 or len(year_users) >= count:
                            break
                        
                        page += 1
                        time.sleep(2) # Stay under 30 req/min limit
                        
                    elif response.status_code == 403:
                        reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
                        sleep_time = max(reset_time - time.time(), 0) + 2
                        print(f"  [Rate Limit Hit] Sleeping for {sleep_time:.0f} seconds...")
                        time.sleep(sleep_time)
                        continue # Retry same page
                    else:
                        print(f"  Error in {state} {year}: HTTP {response.status_code}")
                        break
                        
                except Exception as e:
                    print(f"  Exception in {state} {year}: {e}")
                    break
            
            state_found += len(year_users)
            total_found += len(year_users)
            all_extracted_users.extend(year_users)
            time.sleep(1) # Brief pause between years
            
        log_to_tasks(f"COMPLETED {state}: Extracted {state_found} users.")
    
    # Deduplicate users (some people might have moved states or triggered multiple hits)
    unique_users = {u["username"]: u for u in all_extracted_users}
    final_list = list(unique_users.values())
    
    log_to_tasks(f"DEEP SEARCH COMPLETE. Total Unique Users Extracted: {len(final_list)}")
    print(f"\n--- SEARCH COMPLETE ---")
    print(f"Total Unique Users Extracted: {len(final_list)}")
    
    # Save the actual usernames to CSV so the Scorer can use them
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "sharded_users.csv"
    
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["GitHub Username", "Shard Info", "Profile URL"])
        for u in final_list:
            writer.writerow([u["username"], u["shard_date"], u["html_url"]])
            
    print(f"Saved candidate list to {output_path}")

if __name__ == "__main__":
    run_deep_search()
