"""
Export Candidates for Clay.com LinkedIn Enrichment

Reads scored candidates and exports a CSV optimized for Clay.com upload.
Only includes candidates that don't already have LinkedIn URLs.

Usage:
    python export_for_clay.py

Output:
    output/clay_upload_candidates.csv - Ready to upload to Clay
"""

import csv
import os
from datetime import datetime

def export_for_clay(input_file: str = None, output_file: str = None):
    """
    Export candidates without LinkedIn URLs to Clay-optimized CSV.
    
    Args:
        input_file: Path to scored candidates CSV (default: latest in output/)
        output_file: Path to output CSV (default: output/clay_upload_candidates.csv)
    """
    # Default paths
    if not input_file:
        input_file = "output/deep_scored_candidates_v3.csv"
    
    if not output_file:
        output_file = "output/clay_upload_candidates.csv"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    print("Exporting candidates for Clay.com enrichment...")
    print("=" * 80)
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    print()
    
    candidates_without_linkedin = []
    total_candidates = 0
    candidates_with_linkedin = 0
    
    # Read scored candidates
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_candidates += 1
                
                # Check if LinkedIn URL exists
                linkedin_url = row.get('LinkedIn URL', '').strip()
                
                if not linkedin_url or linkedin_url.lower() == 'n/a':
                    # No LinkedIn URL - needs enrichment
                    candidates_without_linkedin.append({
                        'GitHub Username': row.get('GitHub Username', ''),
                        'Name': row.get('Name', row.get('GitHub Username', '')),
                        'Location': row.get('Location', ''),
                        'Company': row.get('Company', ''),
                        'Overall Score': row.get('Overall Score', ''),
                        'GitHub URL': f"https://github.com/{row.get('GitHub Username', '')}"
                    })
                else:
                    candidates_with_linkedin += 1
    
    except FileNotFoundError:
        print(f"❌ ERROR: Input file not found: {input_file}")
        print("\nPlease run the scorer first:")
        print('python deep_scorer_v3.py "path/to/sharded_users.csv"')
        return
    
    # Write Clay upload CSV
    if candidates_without_linkedin:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['GitHub Username', 'Name', 'Location', 'Company', 'Overall Score', 'GitHub URL']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(candidates_without_linkedin)
        
        print(f"✅ Exported {len(candidates_without_linkedin)} candidates for Clay enrichment")
        print()
        print("Summary:")
        print(f"  Total candidates:          {total_candidates}")
        print(f"  Already have LinkedIn:     {candidates_with_linkedin} ({candidates_with_linkedin/total_candidates*100:.1f}%)")
        print(f"  Need LinkedIn enrichment:  {len(candidates_without_linkedin)} ({len(candidates_without_linkedin)/total_candidates*100:.1f}%)")
        print()
        print("=" * 80)
        print("Next Steps:")
        print()
        print("1. Log into Clay.com")
        print("2. Create new table: 'GitHub Candidates LinkedIn Enrichment'")
        print(f"3. Import this CSV: {output_file}")
        print("4. Add enrichment column: 'Find LinkedIn URL' (use Clearbit, Apollo, or PDL)")
        print("5. Run enrichment (Clay will process automatically)")
        print("6. Export enriched CSV from Clay")
        print("7. Run: python merge_clay_results.py")
        print()
        print("See CLAY_UPLOAD_WORKFLOW.md for detailed instructions")
        print("=" * 80)
    else:
        print("✅ All candidates already have LinkedIn URLs!")
        print("No enrichment needed.")


if __name__ == "__main__":
    export_for_clay()
