import csv
import sys
import os
import random
import time
import datetime
from github import Auth, Github
from pathlib import Path
from dotenv import load_dotenv
from linkedin_extractor import extract_linkedin_from_github_user

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN not found in .env file")

# V3 Rubric - More generous scoring to properly recognize elite candidates
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
    V3 Scorer - More generous algorithm that properly recognizes elite candidates.
    
    Key improvements:
    - More points per repo match (10 → 15)
    - Bonus for high-quality repos (stars, forks)
    - Better recognition of production experience
    - Removed random baseline (only score real skills)
    """
    scores = {dim: 0 for dim in rubric}
    try:
        user = github_client.get_user(username)
        repos = user.get_repos(type="owner", sort="updated")
        
        repo_count = 0
        total_stars = 0
        total_forks = 0
        
        has_go = False
        has_hcl = False
        has_python = False
        
        for repo in repos:
            if repo_count >= 50:
                break
                
            repo_count += 1
            name = (repo.name or "").lower()
            desc = (repo.description or "").lower()
            lang = (repo.language or "").lower()
            
            stars = repo.stargazers_count or 0
            forks = repo.forks_count or 0
            total_stars += stars
            total_forks += forks
            
            # Track languages
            if lang == "go": has_go = True
            if lang == "hcl": has_hcl = True
            if lang == "python": has_python = True
            
            # Quality multiplier based on repo popularity
            quality_multiplier = 1.0
            if stars > 100:
                quality_multiplier = 2.0  # High-quality repo
            elif stars > 20:
                quality_multiplier = 1.5  # Good repo
            elif stars > 5:
                quality_multiplier = 1.2  # Decent repo
            
            # Go_K8s_Operators - More generous scoring
            if "operator" in name or "operator" in desc:
                scores["Go_K8s_Operators"] += int(15 * quality_multiplier)
            if "kubebuilder" in name or "kubebuilder" in desc:
                scores["Go_K8s_Operators"] += int(15 * quality_multiplier)
            if "controller" in name or "controller" in desc:
                scores["Go_K8s_Operators"] += int(12 * quality_multiplier)
            if "kubernetes" in name or "kubernetes" in desc or "k8s" in name or "k8s" in desc:
                scores["Go_K8s_Operators"] += int(8 * quality_multiplier)
                scores["Tooling_Automation"] += int(5 * quality_multiplier)
            
            # IaC_Terraform_Helm - More generous scoring
            if "terraform" in name or "terraform" in desc:
                scores["IaC_Terraform_Helm"] += int(15 * quality_multiplier)
            if "helm" in name or "helm" in desc:
                scores["IaC_Terraform_Helm"] += int(15 * quality_multiplier)
            if "infrastructure" in name or "infrastructure" in desc:
                scores["IaC_Terraform_Helm"] += int(10 * quality_multiplier)
            if lang == "hcl":
                scores["IaC_Terraform_Helm"] += int(8 * quality_multiplier)
            
            # Tooling_Automation - More generous scoring
            if "automation" in name or "automation" in desc:
                scores["Tooling_Automation"] += int(12 * quality_multiplier)
            if "cli" in name or "tool" in name:
                scores["Tooling_Automation"] += int(10 * quality_multiplier)
            if "pipeline" in name or "pipeline" in desc or "ci" in name or "cd" in name:
                scores["Tooling_Automation"] += int(10 * quality_multiplier)
            
            # GitOps - More generous scoring
            if "argo" in name or "argo" in desc:
                scores["GitOps"] += int(15 * quality_multiplier)
            if "flux" in name or "flux" in desc:
                scores["GitOps"] += int(15 * quality_multiplier)
            if "gitops" in name or "gitops" in desc:
                scores["GitOps"] += int(12 * quality_multiplier)
            
            # Storage - More generous scoring
            if "rook" in name or "rook" in desc:
                scores["Storage"] += int(15 * quality_multiplier)
            if "ceph" in name or "ceph" in desc:
                scores["Storage"] += int(15 * quality_multiplier)
            if "storage" in name or "storage" in desc:
                scores["Storage"] += int(10 * quality_multiplier)
            if "weka" in name or "weka" in desc:
                scores["Storage"] += int(12 * quality_multiplier)

        # Cap scores at rubric max
        for dim, max_val in rubric.items():
            scores[dim] = min(scores[dim], max_val)

        # OSS_Familiarity - Based on activity and contributions
        if total_stars > 500:
            scores["OSS_Familiarity"] = 5
        elif total_stars > 100:
            scores["OSS_Familiarity"] = 4
        elif total_stars > 20:
            scores["OSS_Familiarity"] = 3
        elif repo_count > 30:
            scores["OSS_Familiarity"] = 2
        else:
            scores["OSS_Familiarity"] = 1
        
        # Bonus for language proficiency
        language_bonus = 0
        if has_go:
            language_bonus += 3
        if has_hcl:
            language_bonus += 2
        if has_python:
            language_bonus += 1
        
        # Distribute language bonus across relevant dimensions
        if language_bonus > 0:
            if scores["Go_K8s_Operators"] < rubric["Go_K8s_Operators"]:
                boost = min(language_bonus, rubric["Go_K8s_Operators"] - scores["Go_K8s_Operators"])
                scores["Go_K8s_Operators"] += boost
                language_bonus -= boost
            
            if language_bonus > 0 and scores["IaC_Terraform_Helm"] < rubric["IaC_Terraform_Helm"]:
                boost = min(language_bonus, rubric["IaC_Terraform_Helm"] - scores["IaC_Terraform_Helm"])
                scores["IaC_Terraform_Helm"] += boost

        overall = sum(scores.values())
        
        location = user.location if user.location else "Unknown"
        rationale = f"Evaluated {repo_count} recent repos."
        if has_go and has_hcl:
            rationale += " Writes Go & HCL."
        if total_stars > 100:
            rationale += f" High-quality repos ({total_stars} stars)."
            
        risks = []
        
        # Check for non-US location
        loc_lower = location.lower()
        non_us_keywords = ["uk", "united kingdom", "london", "canada", "toronto", "vancouver", 
                          "india", "bangalore", "germany", "australia", "china", "france", 
                          "brazil", "russia", "ukraine", "pakistan"]
        if any(keyword in loc_lower for keyword in non_us_keywords):
            risks.append("Potential Non-US Resident")
        
        risk_str = ", ".join(risks) if risks else "Clear"

        # Extract LinkedIn URL ONLY if explicitly found on GitHub profile
        # Checks: bio, blog/website field, social accounts API
        # NO auto-generation, NO guessing, NO Google fallback
        # Returns None if not explicitly found on profile
        linkedin_url = extract_linkedin_from_github_user(user, verify_guesses=False, use_google_fallback=False)

        return {
            "username": username,
            "overall": overall,
            "repo_count": repo_count,
            "location": location,
            "scores": scores,
            "rationale": rationale,
            "risks": risk_str,
            "stars": total_stars,
            "forks": total_forks,
            "linkedin_url": linkedin_url
        }

    except Exception as e:
        if "API rate limit exceeded" in str(e):
            reset_timestamp = github_client.get_rate_limit().core.reset
            sleep_time = max(0, (reset_timestamp - datetime.datetime.utcnow()).total_seconds()) + 5
            print(f"\n[RATE LIMIT HIT] Sleeping for {sleep_time/60:.1f} minutes until {reset_timestamp} UTC...", file=sys.stderr)
            time.sleep(sleep_time)
            return evaluate_user(username, github_client)
        print(f"Error evaluating {username}: {e}", file=sys.stderr)
        return None

def main():
    # Check for input file
    input_file = None
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    else:
        # Default to existing sharded_users.csv
        input_file = Path("output/sharded_users.csv")
    
    if not input_file.exists():
        print(f"Error: Could not find {input_file}.", file=sys.stderr)
        print("Usage: python deep_scorer_v3.py [input_csv]", file=sys.stderr)
        sys.exit(1)

    usernames = []
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            usernames.append(row["GitHub Username"])

    print(f"Loaded {len(usernames)} users. Beginning V3 Rubric scoring (more generous)...", file=sys.stderr)
    print("V3 improvements: More points per match, quality bonuses, language bonuses", file=sys.stderr)

    data = []
    count = 0
    for username in usernames:
        count += 1
        if count % 50 == 0:
            print(f"Scoring {username} ({count}/{len(usernames)})...", file=sys.stderr)
        result = evaluate_user(username, g)
        
        if result:
            row = [
                result["username"], 
                result["overall"], 
                result["repo_count"], 
                "Deep Search (Multi-Repo)", 
                result["location"]
            ] + list(result["scores"].values()) + [
                result["rationale"], 
                result["risks"],
                result["linkedin_url"] or ""
            ]
            data.append(row)
            
        time.sleep(0.5)

    # Sort by overall score descending
    data.sort(key=lambda x: x[1], reverse=True)

    headers = ['GitHub Username', 'Overall Score', 'Analyzed Repos', 'Source', 'Location'] + list(rubric.keys()) + ['Rationale', 'Risks', 'LinkedIn URL']

    # Write to Output Directory
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "deep_scored_candidates_v3.csv"

    with output_path.open("w", newline="", encoding="utf-8") as f:
        file_writer = csv.writer(f)
        file_writer.writerow(headers)
        file_writer.writerows(data)

    # Also write to stdout
    writer = csv.writer(sys.stdout)
    writer.writerow(headers)
    writer.writerows(data[:20])  # Show top 20

    print(f"\n\nScoring complete. {len(data)} candidates scored and saved to {output_path}", file=sys.stderr)
    
    # Show statistics
    scores_80_plus = sum(1 for row in data if row[1] >= 80)
    scores_70_plus = sum(1 for row in data if row[1] >= 70)
    top_score = data[0][1] if data else 0
    
    # LinkedIn URL statistics (LinkedIn URL is last column)
    linkedin_count = sum(1 for row in data if row[-1])
    linkedin_percent = (linkedin_count / len(data) * 100) if data else 0
    
    print(f"\n=== SCORING STATISTICS ===", file=sys.stderr)
    print(f"Total candidates: {len(data)}", file=sys.stderr)
    print(f"Top score: {top_score}", file=sys.stderr)
    print(f"Candidates scoring 80+: {scores_80_plus}", file=sys.stderr)
    print(f"Candidates scoring 70+: {scores_70_plus}", file=sys.stderr)
    print(f"\n=== LINKEDIN URL EXTRACTION ===", file=sys.stderr)
    print(f"LinkedIn URLs found: {linkedin_count}/{len(data)} ({linkedin_percent:.1f}%)", file=sys.stderr)
    print(f"\nV3 Scoring + LinkedIn extraction complete!", file=sys.stderr)

if __name__ == "__main__":
    main()
