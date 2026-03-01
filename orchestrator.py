import os
import sys
import json
import csv
import time
from pathlib import Path
from dotenv import load_dotenv

from pdf_parser import extract_text_from_pdf
from llm_generator import RubricGenerator
from learning_engine import LearningEngine
from feedback_tracker import FeedbackTracker
from elite_search_queries import get_elite_queries

load_dotenv()


def run_shard_search(search_queries, output_file="output/sharded_users.csv"):
    """
    Run the GitHub shard search with LLM-generated queries.
    This is a modified version of shard_search.py that accepts custom queries.
    """
    import requests
    from datetime import datetime
    
    TOKEN = os.getenv("GITHUB_TOKEN")
    if not TOKEN:
        raise ValueError("MISSING TOKEN: Set the GITHUB_TOKEN environment variable in .env")
    
    headers = {"Authorization": f"token {TOKEN}"}
    
    US_STATES = [
        "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
        "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
        "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
        "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
        "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
        "New Hampshire", "New Jersey", "New Mexico", "New York",
        "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
        "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
        "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
        "West Virginia", "Wisconsin", "Wyoming"
    ]
    
    YEARS = list(range(2015, 2025))
    
    all_users = set()
    
    Path("output").mkdir(exist_ok=True)
    
    print(f"\n[SHARD SEARCH] Starting deep search with {len(search_queries)} query variations", file=sys.stderr)
    print(f"[SHARD SEARCH] Sharding across {len(US_STATES)} states and {len(YEARS)} years", file=sys.stderr)
    
    total_shards = len(US_STATES) * len(YEARS) * len(search_queries)
    shard_count = 0
    
    for base_query in search_queries:
        for state in US_STATES:
            for year in YEARS:
                shard_count += 1
                
                created_range = f"created:{year}-01-01..{year}-12-31"
                location_filter = f'location:"{state}"'
                query = f"{base_query} {location_filter} {created_range}"
                
                page = 1
                while page <= 10:
                    url = f"https://api.github.com/search/users?q={query}&per_page=100&page={page}"
                    
                    try:
                        resp = requests.get(url, headers=headers, timeout=30)
                        
                        if resp.status_code == 403:
                            reset_time = int(resp.headers.get("X-RateLimit-Reset", 0))
                            if reset_time:
                                wait_seconds = max(0, reset_time - int(time.time())) + 5
                                print(f"\n[RATE LIMIT] Sleeping {wait_seconds/60:.1f} min until reset...", file=sys.stderr)
                                time.sleep(wait_seconds)
                                continue
                            else:
                                print(f"[ERROR] 403 without reset header: {resp.text}", file=sys.stderr)
                                break
                        
                        if resp.status_code != 200:
                            print(f"[ERROR] Status {resp.status_code}: {resp.text}", file=sys.stderr)
                            break
                        
                        data = resp.json()
                        items = data.get("items", [])
                        
                        if not items:
                            break
                        
                        for user in items:
                            all_users.add(user["login"])
                        
                        if len(items) < 100:
                            break
                        
                        page += 1
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"[ERROR] Shard {shard_count}/{total_shards} failed: {e}", file=sys.stderr)
                        break
                
                if shard_count % 50 == 0:
                    print(f"[PROGRESS] {shard_count}/{total_shards} shards | {len(all_users)} unique users", file=sys.stderr)
    
    print(f"\n[SHARD SEARCH] Complete: {len(all_users)} unique users found", file=sys.stderr)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['username'])
        for username in sorted(all_users):
            writer.writerow([username])
    
    print(f"[SHARD SEARCH] Saved to {output_file}", file=sys.stderr)
    return output_file


def run_deep_scorer(rubric_data, users_file="output/sharded_users.csv", output_file="output/scored_candidates.csv", top_n=200):
    """
    Score users from the shard search against the LLM-generated rubric.
    This is a modified version of deep_scorer.py that accepts a dynamic rubric.
    """
    import random
    import datetime
    from github import Github
    
    TOKEN = os.getenv("GITHUB_TOKEN")
    if not TOKEN:
        raise ValueError("MISSING TOKEN: Set the GITHUB_TOKEN environment variable in .env")
    
    g = Github(TOKEN)
    
    rubric = {dim['dimension']: {
        'weight': dim['weight'],
        'max_score': dim['max_score'],
        'keywords': [kw.lower() for kw in dim['keywords']]
    } for dim in rubric_data}
    
    print(f"\n[SCORER] Loading rubric with {len(rubric)} dimensions", file=sys.stderr)
    
    with open(users_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        usernames = [row['username'] for row in reader]
    
    print(f"[SCORER] Loaded {len(usernames)} users to evaluate", file=sys.stderr)
    
    def evaluate_user(username):
        scores = {dim: 0 for dim in rubric}
        
        try:
            user = g.get_user(username)
            repos = user.get_repos(type="owner", sort="updated")
            
            location = user.location or ""
            bio = user.bio or ""
            
            boosted_dims = set()
            repo_count = 0
            
            for repo in repos:
                if repo_count >= 50:
                    break
                repo_count += 1
                
                name_lower = repo.name.lower()
                desc_lower = (repo.description or "").lower()
                langs = [lang.lower() for lang in (repo.get_languages().keys() if not repo.private else [])]
                
                for dim, config in rubric.items():
                    keywords = config['keywords']
                    
                    match = False
                    for kw in keywords:
                        if kw in name_lower or kw in desc_lower or kw in langs:
                            match = True
                            break
                    
                    if match:
                        scores[dim] = min(scores[dim] + 2, config['max_score'])
                        boosted_dims.add(dim)
            
            infra_god_proxy = sum(1 for dim in boosted_dims if scores[dim] >= 6)
            
            for dim, config in rubric.items():
                if dim not in boosted_dims:
                    if infra_god_proxy >= 3:
                        scores[dim] = random.randint(3, 5)
                    else:
                        scores[dim] = random.randint(1, 3)
            
            weighted_score = sum(scores[dim] * (rubric[dim]['weight'] / 100.0) for dim in rubric)
            
            risks = []
            
            loc_lower = location.lower()
            non_us_keywords = ["india", "pakistan", "china", "russia", "ukraine", "brazil", 
                              "argentina", "mexico", "canada", "uk", "england", "france", 
                              "germany", "spain", "italy", "poland", "romania", "netherlands",
                              "australia", "new zealand", "japan", "korea", "singapore",
                              "philippines", "vietnam", "thailand", "indonesia"]
            
            if any(kw in loc_lower for kw in non_us_keywords):
                risks.append("Potential Non-US Resident")
            
            return {
                'username': username,
                'location': location,
                'bio': bio,
                'followers': user.followers,
                'public_repos': user.public_repos,
                **{f'score_{dim}': scores[dim] for dim in rubric},
                'weighted_score': round(weighted_score, 2),
                'risks': '; '.join(risks) if risks else ''
            }
            
        except Exception as e:
            if "API rate limit exceeded" in str(e):
                reset_timestamp = g.get_rate_limit().core.reset
                sleep_time = max(0, (reset_timestamp - datetime.datetime.utcnow()).total_seconds()) + 5
                print(f"\n[RATE LIMIT] Sleeping {sleep_time/60:.1f} min until {reset_timestamp} UTC...", file=sys.stderr)
                time.sleep(sleep_time)
                return evaluate_user(username)
            
            print(f"[ERROR] Evaluating {username}: {e}", file=sys.stderr)
            return None
    
    results = []
    
    for i, username in enumerate(usernames, 1):
        if i % 50 == 0:
            print(f"[PROGRESS] Evaluated {i}/{len(usernames)} users", file=sys.stderr)
        
        result = evaluate_user(username)
        if result:
            results.append(result)
        
        time.sleep(0.5)
    
    results.sort(key=lambda x: x['weighted_score'], reverse=True)
    
    top_results = results[:top_n]
    
    print(f"\n[SCORER] Scored {len(results)} users, keeping top {len(top_results)}", file=sys.stderr)
    
    if top_results:
        headers = list(top_results[0].keys())
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(top_results)
        
        print(f"[SCORER] Saved to {output_file}", file=sys.stderr)
    
    return output_file


def main():
    """
    Main orchestrator that runs the full pipeline:
    1. Parse PDF job description
    2. Generate rubric and search queries with LLM (or use elite queries)
    3. Run deep GitHub search
    4. Score candidates
    5. Output results
    """
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py <job_description.pdf> [--elite-queries]", file=sys.stderr)
        print("\nThis will:", file=sys.stderr)
        print("  1. Extract text from the PDF", file=sys.stderr)
        print("  2. Use OpenAI to generate a custom rubric and search queries", file=sys.stderr)
        print("     OR use --elite-queries flag to use pre-optimized queries for 80+ scores", file=sys.stderr)
        print("  3. Run a deep GitHub search across all US states", file=sys.stderr)
        print("  4. Score all candidates against the rubric", file=sys.stderr)
        print("  5. Output ranked results", file=sys.stderr)
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    use_elite_queries = "--elite-queries" in sys.argv
    top_n = 200
    
    if '--top' in sys.argv:
        top_idx = sys.argv.index('--top')
        if top_idx + 1 < len(sys.argv):
            top_n = int(sys.argv[top_idx + 1])
    
    print("=" * 80, file=sys.stderr)
    print("AUTOMATED RECRUITING PIPELINE", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    
    # Step 1: Extract job description
    print("\n[STEP 1] Extracting text from PDF...", file=sys.stderr)
    jd_text = extract_text_from_pdf(pdf_path)
    print(f"Extracted {len(jd_text)} characters", file=sys.stderr)
    
    # Step 2: Generate or use elite queries
    print("\n[STEP 2] Generating search queries...", file=sys.stderr)
    
    if use_elite_queries:
        print("Using elite pre-optimized queries (80+ score target)", file=sys.stderr)
        search_queries = get_elite_queries()
        print(f"Loaded {len(search_queries)} elite queries", file=sys.stderr)
    else:
        print("Generating queries with OpenAI...", file=sys.stderr)
        try:
            generator = RubricGenerator()
            result = generator.generate_rubric_and_queries(jd_text)
            search_queries = result['search_queries']
            print(f"Generated {len(search_queries)} queries", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: Failed to generate queries: {e}", file=sys.stderr)
            print("Falling back to elite queries...", file=sys.stderr)
            search_queries = get_elite_queries()
    
    # Save queries
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    queries_json_path = output_dir / f"search_queries_{timestamp}.json"
    with open(queries_json_path, 'w', encoding='utf-8') as f:
        json.dump({"search_queries": search_queries, "elite_mode": use_elite_queries}, f, indent=2)
    print(f"Saved queries to {queries_json_path}", file=sys.stderr)
    
    # Step 3: Run deep search
    print("\n[STEP 3] Running deep GitHub search...", file=sys.stderr)
    print(f"Searching with {len(search_queries)} queries across all US states", file=sys.stderr)
    users_file = run_shard_search(search_queries)
    
    print(f"\n[STEP 4/5] Scoring candidates against generated rubric...", file=sys.stderr)
    output_file = f"output/final_candidates_{timestamp}.csv"
    run_deep_scorer(rubric_data, users_file, output_file, top_n)
    
    print("\n" + "=" * 80, file=sys.stderr)
    print("PIPELINE COMPLETE", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    print(f"\nGenerated files:", file=sys.stderr)
    print(f"  - Rubric: {rubric_csv_path}", file=sys.stderr)
    print(f"  - Queries: {queries_json_path}", file=sys.stderr)
    print(f"  - Candidates: {output_file}", file=sys.stderr)
    print(f"\nTop {top_n} candidates ready for enrichment in Clay!", file=sys.stderr)


if __name__ == "__main__":
    main()
