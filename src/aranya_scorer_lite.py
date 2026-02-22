#!/usr/bin/env python3
"""
Lightweight GitHub sourcing script - no user location lookups (faster)
"""
import csv
import sys
from github import Github
import random
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN not found in .env file")

REPOS_TO_SCAN = [
    "argoproj/argo-cd",
    "kubernetes/kubernetes",
    "cilium/cilium",
    "rook/rook",
    "ceph/ceph-csi-operator",
    "operator-framework/operator-sdk",
    "prometheus-operator/prometheus-operator",
]

MIN_COMMITS = 10
TOP_N_PER_REPO = 50

rubric = {
    'Operators': 20,
    'GitOps': 15,
    'Storage': 10,
    'Networking': 10,
    'MultiCluster': 10,
    'IaC': 10,
    'Observability': 10,
    'OSS': 10,
    'Product': 5
}

g = Github(GITHUB_TOKEN, per_page=30)  # Optimize pagination

contributors = []
for repo_name in REPOS_TO_SCAN:
    try:
        print(f"Scanning {repo_name}...", file=sys.stderr)
        repo = g.get_repo(repo_name)
        contribs = repo.get_contributors()
        
        count = 0
        for c in contribs:
            if count >= TOP_N_PER_REPO:
                break
            if c.contributions >= MIN_COMMITS:
                contrib = {
                    "username": c.login, 
                    "commits": c.contributions, 
                    "repo": repo_name, 
                    "location": "US"  # Default, since user lookups are slow
                }
                contributors.append(contrib)
                count += 1
                if count % 20 == 0:
                    print(f"  ... {count} contributors", file=sys.stderr)
        
        print(f"✓ {repo_name}: {count} contributors", file=sys.stderr)
    except Exception as e:
        print(f"✗ {repo_name}: {str(e)}", file=sys.stderr)

# Deduplicate
unique_contribs = {c["username"]: c for c in contributors}
contributors = list(unique_contribs.values())

print(f"Total unique candidates: {len(contributors)}", file=sys.stderr)

# Output CSV
data = []
for contrib in contributors:
    username = contrib["username"]
    commits = contrib["commits"]
    repo = contrib["repo"]
    location = contrib["location"]

    scores = {dim: random.randint(0, rubric[dim] // 3) for dim in rubric}
    
    # Boost based on repo
    if "argo" in repo.lower():
        scores["GitOps"] = min(15, 10 + (commits // 10))
        scores["Operators"] = min(20, 12 + (commits // 20))
    if "kubernetes" in repo.lower():
        scores["Operators"] = min(20, scores["Operators"] + 8)
        scores["MultiCluster"] = min(10, scores["MultiCluster"] + 5)
    if "cilium" in repo.lower():
        scores["Networking"] = min(10, 8 + (commits // 50))
    if "rook" in repo.lower() or "ceph" in repo.lower():
        scores["Storage"] = min(10,8 + (commits // 50))
    if "operator" in repo.lower():
        scores["Operators"] = min(20, scores["Operators"] + 5)
    if "prometheus" in repo.lower():
        scores["Observability"] = min(10, 7 + (commits // 50))

    overall = sum(scores.values())
    rationale = f"From {repo} ({commits} commits)."
    risks = "GH contributor"

    row = [username, overall, commits, repo, location] + list(scores.values()) + [rationale, risks]
    data.append(row)

data.sort(key=lambda x: x[1], reverse=True)

headers = ['GitHub Username', 'Overall Score', 'Commits', 'Repo', 'Location'] + list(rubric.keys()) + ['Rationale', 'Risks']

output_dir = Path(__file__).resolve().parents[1] / "output"
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / "candidates_lite.csv"

with output_path.open("w", newline="", encoding="utf-8") as f:
    file_writer = csv.writer(f)
    file_writer.writerow(headers)
    file_writer.writerows(data)

writer = csv.writer(sys.stdout)
writer.writerow(headers)
writer.writerows(data)

print(f"Done. {len(data)} candidates output.", file=sys.stderr)
