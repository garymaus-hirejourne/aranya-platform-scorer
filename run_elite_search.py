"""
Simple script to run the pipeline with elite queries for 80+ scoring candidates.

Usage: python run_elite_search.py
"""

import os
import sys
import subprocess
from pathlib import Path
from elite_search_queries import get_elite_queries

def main():
    print("=" * 80)
    print("ELITE CANDIDATE SEARCH - Target: 80+ Scores")
    print("=" * 80)
    print()
    
    # Get elite queries
    queries = get_elite_queries()
    print(f"Using {len(queries)} elite-optimized search queries:")
    for i, query in enumerate(queries, 1):
        print(f"  {i}. {query}")
    print()
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Write queries to file for shard_search.py to use
    queries_file = output_dir / "elite_queries.txt"
    with open(queries_file, 'w', encoding='utf-8') as f:
        for query in queries:
            f.write(query + '\n')
    
    print(f"Saved queries to: {queries_file}")
    print()
    
    # Step 1: Run shard search with elite queries
    print("[STEP 1/2] Running deep GitHub search...")
    print("This will search across all US states and may take 30-60 minutes.")
    print()
    
    # Run shard_search.py (it will use the queries)
    try:
        result = subprocess.run(
            [sys.executable, "shard_search.py"],
            cwd=Path(__file__).parent,
            capture_output=False,
            text=True
        )
        
        if result.returncode != 0:
            print(f"ERROR: shard_search.py failed with code {result.returncode}")
            return
    except Exception as e:
        print(f"ERROR running shard_search.py: {e}")
        return
    
    # Step 2: Run deep scorer
    print()
    print("[STEP 2/2] Scoring candidates with rubric v2...")
    print("This will evaluate all found candidates.")
    print()
    
    try:
        result = subprocess.run(
            [sys.executable, "deep_scorer.py"],
            cwd=Path(__file__).parent,
            capture_output=False,
            text=True
        )
        
        if result.returncode != 0:
            print(f"ERROR: deep_scorer.py failed with code {result.returncode}")
            return
    except Exception as e:
        print(f"ERROR running deep_scorer.py: {e}")
        return
    
    print()
    print("=" * 80)
    print("SEARCH COMPLETE")
    print("=" * 80)
    print()
    print("Output files:")
    print("  - output/sharded_users.csv (all found candidates)")
    print("  - output/deep_scored_candidates.csv (scored and ranked)")
    print()
    print("Check the top of deep_scored_candidates.csv for 80+ scoring candidates!")
    print()

if __name__ == "__main__":
    main()
