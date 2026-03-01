"""
Quick test script to verify LinkedIn extraction works on a few sample candidates
"""

import os
from dotenv import load_dotenv
from github import Auth, Github
from linkedin_extractor import extract_linkedin_from_github_user

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
g = Github(auth=Auth.Token(GITHUB_TOKEN))

# Test on top 5 candidates from previous scoring
test_usernames = [
    "mmerrill3",      # Score 93
    "phamcs",         # Score 88
    "pkoppa",         # Score 82
    "ssung-yugabyte", # Score 78
    "bindrad"         # Score 73
]

print("Testing LinkedIn URL extraction on top 5 candidates...\n")
print("=" * 80)

for username in test_usernames:
    try:
        user = g.get_user(username)
        linkedin_url = extract_linkedin_from_github_user(user, verify_guesses=False)
        
        print(f"\nUsername: {username}")
        print(f"Name: {user.name}")
        print(f"Bio: {user.bio}")
        print(f"Blog: {user.blog}")
        print(f"LinkedIn URL: {linkedin_url or 'NOT FOUND'}")
        print("-" * 80)
    except Exception as e:
        print(f"\nError testing {username}: {e}")
        print("-" * 80)

print("\nTest complete!")
