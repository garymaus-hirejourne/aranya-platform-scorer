"""
Merge Clay.com Enrichment Results

Merges LinkedIn URLs from Clay enrichment back into the scored candidates CSV.

Usage:
    python merge_clay_results.py

Input:
    output/deep_scored_candidates_v3.csv - Original scored candidates
    output/clay_enriched_results.csv - Enriched results from Clay

Output:
    output/deep_scored_candidates_v3_enriched.csv - Merged results
"""

import csv
import os
from datetime import datetime

def merge_clay_results(
    scored_file: str = None,
    clay_file: str = None,
    output_file: str = None
):
    """
    Merge LinkedIn URLs from Clay enrichment into scored candidates.
    
    Args:
        scored_file: Original scored candidates CSV
        clay_file: Clay enrichment results CSV
        output_file: Output merged CSV
    """
    # Default paths
    if not scored_file:
        scored_file = "output/deep_scored_candidates_v3.csv"
    
    if not clay_file:
        clay_file = "output/clay_enriched_results.csv"
    
    if not output_file:
        output_file = "output/deep_scored_candidates_v3_enriched.csv"
    
    print("Merging Clay.com enrichment results...")
    print("=" * 80)
    print(f"Scored candidates: {scored_file}")
    print(f"Clay results:      {clay_file}")
    print(f"Output:            {output_file}")
    print()
    
    # Read Clay enrichment results into dictionary
    clay_linkedin = {}
    clay_found = 0
    
    try:
        with open(clay_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                github_username = row.get('GitHub Username', '').strip()
                
                # Clay may use different column names - try common variations
                linkedin_url = (
                    row.get('LinkedIn URL') or 
                    row.get('linkedin_url') or 
                    row.get('Contact Linkedin URL') or
                    row.get('Person LinkedIn URL') or
                    ''
                ).strip()
                
                if github_username and linkedin_url and linkedin_url.lower() != 'n/a':
                    clay_linkedin[github_username] = linkedin_url
                    clay_found += 1
        
        print(f"✅ Loaded {clay_found} LinkedIn URLs from Clay")
        
    except FileNotFoundError:
        print(f"❌ ERROR: Clay results file not found: {clay_file}")
        print("\nPlease:")
        print("1. Download enriched CSV from Clay.com")
        print(f"2. Save it as: {clay_file}")
        print("3. Run this script again")
        return
    
    # Read scored candidates and merge
    merged_candidates = []
    total_candidates = 0
    already_had_linkedin = 0
    newly_enriched = 0
    still_missing = 0
    
    try:
        with open(scored_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            for row in reader:
                total_candidates += 1
                github_username = row.get('GitHub Username', '').strip()
                existing_linkedin = row.get('LinkedIn URL', '').strip()
                
                # Check if already has LinkedIn
                if existing_linkedin and existing_linkedin.lower() != 'n/a':
                    already_had_linkedin += 1
                    merged_candidates.append(row)
                # Check if Clay found LinkedIn
                elif github_username in clay_linkedin:
                    row['LinkedIn URL'] = clay_linkedin[github_username]
                    newly_enriched += 1
                    merged_candidates.append(row)
                else:
                    # Still no LinkedIn URL
                    still_missing += 1
                    merged_candidates.append(row)
        
        # Write merged results
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(merged_candidates)
        
        print()
        print("=" * 80)
        print("Merge Complete!")
        print("=" * 80)
        print()
        print("Summary:")
        print(f"  Total candidates:           {total_candidates}")
        print(f"  Already had LinkedIn:       {already_had_linkedin} ({already_had_linkedin/total_candidates*100:.1f}%)")
        print(f"  Newly enriched from Clay:   {newly_enriched} ({newly_enriched/total_candidates*100:.1f}%)")
        print(f"  Total with LinkedIn:        {already_had_linkedin + newly_enriched} ({(already_had_linkedin + newly_enriched)/total_candidates*100:.1f}%)")
        print(f"  Still missing LinkedIn:     {still_missing} ({still_missing/total_candidates*100:.1f}%)")
        print()
        print(f"✅ Merged results saved to: {output_file}")
        print()
        
        if still_missing > 0:
            print("⚠️ Note: Some candidates still don't have LinkedIn URLs.")
            print("   This is normal - not everyone has a public LinkedIn profile.")
            print("   Focus on the candidates with high scores who have LinkedIn URLs.")
        
        print("=" * 80)
        
    except FileNotFoundError:
        print(f"❌ ERROR: Scored candidates file not found: {scored_file}")
        print("\nPlease run the scorer first:")
        print('python deep_scorer_v3.py "path/to/sharded_users.csv"')
        return


if __name__ == "__main__":
    merge_clay_results()
