"""
Investigate why wrong candidates are being enriched.

Check if the problem is:
1. GitHub profiles are wrong (search found wrong people)
2. LinkedIn URLs are mismatched (wrong LinkedIn for right GitHub)
3. Scoring is wrong (scoring irrelevant repos highly)
"""

import os
from dotenv import load_dotenv
from github import Auth, Github

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
g = Github(auth=Auth.Token(GITHUB_TOKEN))

# Top 10 GitHub usernames from scoring
top_candidates = [
    "mmerrill3",      # Score 93
    "phamcs",         # Score 88
    "pkoppa",         # Score 82
    "ssung-yugabyte", # Score 78
    "bindrad",        # Score 73
    "turnbros",       # Score 72
    "jeff-roche",     # Score 70
    "sphara-app",     # Score 70
    "camartinez04",   # Score 67
    "oluwa200"        # Score 67
]

print("=" * 100)
print("INVESTIGATING TOP 10 CANDIDATES")
print("=" * 100)
print("\nChecking if GitHub profiles match Kubernetes/Platform Engineer criteria...")
print()

for username in top_candidates:
    try:
        user = g.get_user(username)
        
        print(f"\n{'='*100}")
        print(f"GitHub Username: {username}")
        print(f"Name: {user.name}")
        print(f"Bio: {user.bio}")
        print(f"Company: {user.company}")
        print(f"Location: {user.location}")
        print(f"Blog: {user.blog}")
        print(f"Public Repos: {user.public_repos}")
        
        # Check recent repos
        print(f"\nRecent Repositories (top 10):")
        repos = list(user.get_repos(type="owner", sort="updated"))[:10]
        
        k8s_count = 0
        terraform_count = 0
        operator_count = 0
        
        for i, repo in enumerate(repos, 1):
            name = repo.name.lower()
            desc = (repo.description or "").lower()
            lang = repo.language or "None"
            stars = repo.stargazers_count
            
            # Check for Kubernetes/Platform keywords
            is_k8s = "kubernetes" in name or "k8s" in name or "kubernetes" in desc or "k8s" in desc
            is_terraform = "terraform" in name or "terraform" in desc
            is_operator = "operator" in name or "operator" in desc
            
            if is_k8s: k8s_count += 1
            if is_terraform: terraform_count += 1
            if is_operator: operator_count += 1
            
            marker = ""
            if is_k8s: marker += "[K8S] "
            if is_terraform: marker += "[TERRAFORM] "
            if is_operator: marker += "[OPERATOR] "
            
            print(f"  {i}. {repo.name} ({lang}, {stars}★) {marker}")
            if repo.description:
                print(f"     {repo.description[:80]}")
        
        print(f"\nKeyword Summary:")
        print(f"  - Kubernetes/K8s repos: {k8s_count}")
        print(f"  - Terraform repos: {terraform_count}")
        print(f"  - Operator repos: {operator_count}")
        
        # Verdict
        if k8s_count >= 2 or operator_count >= 1 or terraform_count >= 2:
            print(f"\n✅ VERDICT: GOOD FIT - Has relevant Kubernetes/Platform repos")
        else:
            print(f"\n❌ VERDICT: BAD FIT - No relevant Kubernetes/Platform repos")
        
    except Exception as e:
        print(f"\nError checking {username}: {e}")

print("\n" + "=" * 100)
print("INVESTIGATION COMPLETE")
print("=" * 100)
