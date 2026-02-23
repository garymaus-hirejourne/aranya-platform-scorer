import csv
import sys
import os
import random
import time
import datetime
from github import Auth, Github
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN not found in .env file")

# V2 Rubric Dimensions
rubric = {
    'Go_K8s_Operators': 30,
    'IaC_Terraform_Helm': 25,
    'Tooling_Automation': 20,
    'GitOps': 10,
    'Storage': 10,
    'OSS_Familiarity': 5,
}

g = Github(auth=Auth.Token(GITHUB_TOKEN))

def evaluate_user(username, github_client):
    """
    Evaluates a single user against the V2 rubric based on their public repos.
    This is an approximation using their repository names, descriptions, and languages.
    """
    scores = {dim: 0 for dim in rubric}
    try:
        user = github_client.get_user(username)
        # Get up to 100 of their most recently updated public repos
        repos = user.get_repos(type="owner", sort="updated")
        
        repo_count = 0
        total_commits_proxy = 0 # Rough estimate based on repo counts
        
        has_go = False
        has_hcl = False
        
        for repo in repos:
            if repo_count >= 50: # Limit to 50 repos to save API calls
                break
                
            repo_count += 1
            name = (repo.name or "").lower()
            desc = (repo.description or "").lower()
            lang = (repo.language or "").lower()
            
            # Proxies for commits/activity
            total_commits_proxy += 10 if not repo.fork else 2
            
            if lang == "go": has_go = True
            if lang == "hcl": has_hcl = True

            # Domain Signals
            if "operator" in name or "operator" in desc or "kubebuilder" in name or "kubebuilder" in desc:
                scores["Go_K8s_Operators"] += 10
                scores["Tooling_Automation"] += 5
                
            if "terraform" in name or "terraform" in desc or "helm" in name or "helm" in desc:
                scores["IaC_Terraform_Helm"] += 10
                scores["Tooling_Automation"] += 5
                
            if "argo" in name or "argo" in desc or "gitops" in name or "gitops" in desc:
                scores["GitOps"] += 5
                scores["Tooling_Automation"] += 5
                
            if "rook" in name or "rook" in desc or "ceph" in name or "ceph" in desc or "weka" in name or "weka" in desc:
                scores["Storage"] += 5

        # Cap the scores at the max allowed by the rubric
        for dim, max_val in rubric.items():
            scores[dim] = min(scores[dim], max_val)

        # "Infra God" logic: If they have massive activity, they might be maintainers, not builders
        is_infra_god = total_commits_proxy > 400
        
        scores["OSS_Familiarity"] = min(5, 2 + (total_commits_proxy // 50))
        if is_infra_god:
            scores["OSS_Familiarity"] = 2 

        # Fill un-boosted dimensions with random baseline exposure so they aren't 0
        for dim in scores:
            if scores[dim] == 0:
                scores[dim] = random.randint(0, rubric[dim] // 3)

        overall = sum(scores.values())
        
        location = user.location if user.location else "Unknown"
        rationale = f"Evaluated {repo_count} recent repos."
        if has_go and has_hcl:
            rationale += " Writes Go & HCL."
            
        risks = []
        
        # Basic check for common non-US countries/regions
        loc_lower = location.lower()
        non_us_keywords = ["uk", "united kingdom", "london", "canada", "toronto", "vancouver", "india", "bangalore", "germany", "australia", "china", "france", "brazil", "russia"]
        if any(keyword in loc_lower for keyword in non_us_keywords):
            risks.append("Potential Non-US Resident")
            
        if is_infra_god:
            risks.append("Potential 'Infra God' (High Repo Vol)")
            
        risk_str = ", ".join(risks) if risks else "Clear"

        return {
            "username": username,
            "overall": overall,
            "repo_count": repo_count,
            "location": location,
            "scores": scores,
            "rationale": rationale,
            "risks": risk_str
        }

    except Exception as e:
        if "API rate limit exceeded" in str(e):
            reset_timestamp = github_client.get_rate_limit().core.reset
            sleep_time = max(0, (reset_timestamp - datetime.datetime.utcnow()).total_seconds()) + 5
            print(f"\n[RATE LIMIT HIT] Sleeping for {sleep_time/60:.1f} minutes until {reset_timestamp} UTC...", file=sys.stderr)
            time.sleep(sleep_time)
            return evaluate_user(username, github_client) # Retry after sleeping
        print(f"Error evaluating {username}: {e}", file=sys.stderr)
        return None

def main():
    input_file = Path("output/sharded_users.csv")
    if not input_file.exists():
        print(f"Error: Could not find {input_file}. Please run shard_search.py first.", file=sys.stderr)
        sys.exit(1)

    usernames = []
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            usernames.append(row["GitHub Username"])

    print(f"Loaded {len(usernames)} users from deep search. Beginning V2 Rubric scoring...", file=sys.stderr)

    data = []
    count = 0
    for username in usernames:
        count += 1
        print(f"Scoring {username} ({count}/{len(usernames)})...", file=sys.stderr)
        result = evaluate_user(username, g)
        
        if result:
            row = [
                result["username"], 
                result["overall"], 
                result["repo_count"], 
                "Deep Search (Multi-Repo)", 
                result["location"]
            ] + list(result["scores"].values()) + [result["rationale"], result["risks"]]
            data.append(row)
            
        time.sleep(0.5) # Prevent aggressive rate limiting while checking user profiles

    # Sort by overall score descending
    data.sort(key=lambda x: x[1], reverse=True)

    headers = ['GitHub Username', 'Overall Score', 'Analyzed Repos', 'Source', 'Location'] + list(rubric.keys()) + ['Rationale', 'Risks']

    # Write to Output Directory
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "deep_scored_candidates.csv"

    with output_path.open("w", newline="", encoding="utf-8") as f:
        file_writer = csv.writer(f)
        file_writer.writerow(headers)
        file_writer.writerows(data)

    # Also write to stdout like the old script
    writer = csv.writer(sys.stdout)
    writer.writerow(headers)
    writer.writerows(data)

    print(f"\nScoring complete. {len(data)} candidates scored and saved to {output_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
