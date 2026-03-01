import pandas as pd
import sys
from pathlib import Path

def merge_scored_with_enriched(scored_path, enriched_path, output_path):
    """
    Merge scored candidates CSV with enriched results CSV based on first and last names.
    
    Args:
        scored_path: Path to scored candidates CSV (has GitHub Username)
        enriched_path: Path to enriched results CSV (has first_name, last_name)
        output_path: Path for merged output CSV
    """
    print(f"\nLoading scored candidates from: {scored_path}")
    df_scored = pd.read_csv(scored_path)
    print(f"  - Loaded {len(df_scored)} scored candidates")
    
    print(f"\nLoading enriched results from: {enriched_path}")
    df_enriched = pd.read_csv(enriched_path)
    print(f"  - Loaded {len(df_enriched)} enriched candidates")
    
    # Clean up column names
    df_enriched.columns = df_enriched.columns.str.strip()
    df_scored.columns = df_scored.columns.str.strip()
    
    # Extract first and last names from enriched data
    print("\nPreparing merge keys...")
    df_enriched['merge_key'] = (
        df_enriched['first_name'].str.lower().str.strip() + '_' + 
        df_enriched['last_name'].str.lower().str.strip()
    )
    
    # For scored data, we need to extract names from GitHub username or use LinkedIn
    # First, let's check if there's a name column we can use
    print(f"\nScored CSV columns: {list(df_scored.columns)}")
    print(f"Enriched CSV columns: {list(df_enriched.columns)}")
    
    # Extract LinkedIn username from enriched file's linkedin column
    # LinkedIn URLs are like: https://www.linkedin.com/in/adamwshero
    # We want to extract "adamwshero" and match it with GitHub username
    
    if 'linkedin' in df_enriched.columns:
        print("\nExtracting LinkedIn usernames from URLs...")
        df_enriched['linkedin_username'] = df_enriched['linkedin'].str.extract(r'/in/([^/]+)/?$')[0]
        df_enriched['linkedin_username'] = df_enriched['linkedin_username'].str.lower().str.strip()
        
        # Clean GitHub usernames
        df_scored['github_username_clean'] = df_scored['GitHub Username'].str.lower().str.strip()
        
        print("\nMerging by username match (GitHub <-> LinkedIn)...")
        merged = df_scored.merge(
            df_enriched,
            left_on='github_username_clean',
            right_on='linkedin_username',
            how='left',
            suffixes=('', '_enriched')
        )
        
        match_count = merged['first_name'].notna().sum()
        print(f"  - Matched {match_count} candidates by username")
    else:
        # Fallback: try to extract names from GitHub username
        print("\nNo LinkedIn column found. Attempting to extract names from GitHub usernames...")
        
        # This is a best-effort approach - GitHub usernames don't always contain real names
        def extract_name_from_username(username):
            """Try to extract first/last name from GitHub username."""
            if pd.isna(username):
                return None, None
            
            # Remove common prefixes/suffixes
            clean = username.lower().replace('-', ' ').replace('_', ' ')
            parts = clean.split()
            
            if len(parts) >= 2:
                return parts[0], parts[-1]
            elif len(parts) == 1:
                return parts[0], ''
            else:
                return None, None
        
        df_scored[['extracted_first', 'extracted_last']] = df_scored['GitHub Username'].apply(
            lambda x: pd.Series(extract_name_from_username(x))
        )
        
        df_scored['merge_key'] = (
            df_scored['extracted_first'].fillna('').str.lower() + '_' + 
            df_scored['extracted_last'].fillna('').str.lower()
        )
        
        print("\nMerging by extracted names...")
        merged = df_scored.merge(
            df_enriched,
            on='merge_key',
            how='left',
            suffixes=('', '_enriched')
        )
        
        match_count = merged['first_name'].notna().sum()
        print(f"  - Matched {match_count} candidates by name extraction")
    
    # Clean up temporary columns
    temp_cols = ['linkedin_username', 'github_username_clean', 'merge_key', 'extracted_first', 'extracted_last']
    cols_to_drop = [col for col in temp_cols if col in merged.columns]
    if cols_to_drop:
        merged = merged.drop(columns=cols_to_drop)
    
    # Save merged results
    print(f"\nSaving merged results to: {output_path}")
    merged.to_csv(output_path, index=False)
    
    # Print summary
    total = len(merged)
    matched = merged['first_name'].notna().sum()
    unmatched = total - matched
    
    print("\n" + "="*80)
    print("MERGE SUMMARY")
    print("="*80)
    print(f"Total scored candidates:     {total}")
    print(f"Successfully matched:        {matched} ({matched/total*100:.1f}%)")
    print(f"Not matched (no enrichment): {unmatched} ({unmatched/total*100:.1f}%)")
    print(f"\nOutput file: {output_path}")
    print("="*80 + "\n")
    
    return merged


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python merge_by_name.py <scored_csv> <enriched_csv> <output_csv>")
        print("\nExample:")
        print('  python merge_by_name.py "scored.csv" "enriched.csv" "merged_output.csv"')
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
    merge_scored_with_enriched(scored_path, enriched_path, output_path)
