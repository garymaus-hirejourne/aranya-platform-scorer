import pandas as pd
import sys
from pathlib import Path

def merge_by_names(scored_path, enriched_path, output_path):
    """
    Merge scored candidates with enriched results by matching first and last names.
    
    The scored file has GitHub usernames but no names.
    The enriched file has first_name and last_name.
    
    We'll need to manually map or use a lookup table.
    """
    print(f"\nLoading scored candidates from: {scored_path}")
    df_scored = pd.read_csv(scored_path)
    print(f"  - Loaded {len(df_scored)} scored candidates")
    
    print(f"\nLoading enriched results from: {enriched_path}")
    df_enriched = pd.read_csv(enriched_path)
    print(f"  - Loaded {len(df_enriched)} enriched candidates")
    
    # Extract LinkedIn username from enriched file
    df_enriched['linkedin_username'] = df_enriched['linkedin'].str.extract(r'/in/([^/]+)/?$')[0]
    df_enriched['linkedin_username'] = df_enriched['linkedin_username'].str.lower().str.strip()
    
    # Clean GitHub usernames
    df_scored['github_username_clean'] = df_scored['GitHub Username'].str.lower().str.strip()
    
    # Strategy 1: Direct username match (GitHub == LinkedIn username)
    print("\n=== STRATEGY 1: Direct Username Match ===")
    merged = df_scored.merge(
        df_enriched,
        left_on='github_username_clean',
        right_on='linkedin_username',
        how='left',
        suffixes=('', '_enriched')
    )
    
    direct_matches = merged['first_name'].notna().sum()
    print(f"Direct matches: {direct_matches}")
    
    # Strategy 2: Fuzzy name matching for remaining candidates
    # Create a lookup of enriched candidates by name
    print("\n=== STRATEGY 2: Creating Name Lookup ===")
    
    # For unmatched candidates, we need to manually create a mapping
    # or use the enriched file's full_name to search
    unmatched = merged[merged['first_name'].isna()].copy()
    print(f"Unmatched candidates: {len(unmatched)}")
    
    # Create a simple name-based lookup from enriched data
    enriched_lookup = {}
    for _, row in df_enriched.iterrows():
        # Create multiple lookup keys
        first = str(row['first_name']).lower().strip()
        last = str(row['last_name']).lower().strip()
        full = str(row['full_name']).lower().strip()
        
        # Store by various keys
        enriched_lookup[f"{first}_{last}"] = row
        enriched_lookup[f"{first}{last}"] = row
        enriched_lookup[full.replace(' ', '')] = row
        enriched_lookup[full.replace(' ', '_')] = row
        
        # Also try GitHub username if it contains name parts
        github_from_linkedin = str(row['linkedin_username']).lower()
        if github_from_linkedin and github_from_linkedin != 'nan':
            enriched_lookup[github_from_linkedin] = row
    
    print(f"Created lookup with {len(enriched_lookup)} keys")
    
    # Try to match unmatched candidates
    print("\n=== STRATEGY 3: Fuzzy Matching ===")
    additional_matches = 0
    
    for idx, row in unmatched.iterrows():
        github_user = str(row['github_username_clean']).lower()
        
        # Try various transformations of GitHub username
        possible_keys = [
            github_user,
            github_user.replace('-', ''),
            github_user.replace('_', ''),
            github_user.replace('-', '_'),
            github_user.replace('_', ''),
        ]
        
        # Try to find a match
        for key in possible_keys:
            if key in enriched_lookup:
                enriched_row = enriched_lookup[key]
                # Update the merged dataframe
                for col in df_enriched.columns:
                    if col not in ['github_username_clean', 'linkedin_username']:
                        merged.at[idx, col] = enriched_row[col]
                additional_matches += 1
                break
    
    print(f"Additional fuzzy matches: {additional_matches}")
    
    # Clean up temporary columns
    temp_cols = ['linkedin_username', 'github_username_clean']
    cols_to_drop = [col for col in temp_cols if col in merged.columns]
    if cols_to_drop:
        merged = merged.drop(columns=cols_to_drop)
    
    # Save merged results
    print(f"\nSaving merged results to: {output_path}")
    merged.to_csv(output_path, index=False)
    
    # Print summary
    total = len(merged)
    matched = merged['first_name'].notna().sum()
    unmatched_final = total - matched
    
    print("\n" + "="*80)
    print("MERGE SUMMARY")
    print("="*80)
    print(f"Total scored candidates:     {total}")
    print(f"Successfully matched:        {matched} ({matched/total*100:.1f}%)")
    print(f"  - Direct username matches: {direct_matches}")
    print(f"  - Fuzzy name matches:      {additional_matches}")
    print(f"Not matched (no enrichment): {unmatched_final} ({unmatched_final/total*100:.1f}%)")
    print(f"\nOutput file: {output_path}")
    print("="*80 + "\n")
    
    # Show sample of matched candidates
    print("\nSample of matched candidates:")
    matched_sample = merged[merged['first_name'].notna()][['GitHub Username', 'Overall Score', 'first_name', 'last_name', 'email1', 'phone1']].head(10)
    print(matched_sample.to_string(index=False))
    
    return merged


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python merge_by_actual_names.py <scored_csv> <enriched_csv> <output_csv>")
        print("\nExample:")
        print('  python merge_by_actual_names.py "scored.csv" "enriched.csv" "merged_output.csv"')
        sys.exit(1)
    
    scored_path = sys.argv[1]
    enriched_path = sys.argv[2]
    output_path = sys.argv[3]
    
    # Verify files exist
    if not Path(scored_path).exists():
        print(f"Error: Scored file not found: {scored_path}")
        sys.exit(1)
    
    if not Path(enriched_path).exists():
        print(f"Error: Enriched file not found: {enriched_path}")
        sys.exit(1)
    
    # Perform merge
    merge_by_names(scored_path, enriched_path, output_path)
