"""
Create a manual verification worksheet for top candidates.

This script generates an Excel file with the top 20-50 candidates
that need manual LinkedIn verification.

Includes:
- GitHub username
- Name from GitHub
- Location
- Score
- GitHub profile URL
- LinkedIn URL (if found)
- Empty column for manual LinkedIn URL entry
- Notes column
"""

import pandas as pd
import sys
from pathlib import Path

def create_verification_sheet(input_csv, output_xlsx, top_n=50):
    """
    Create manual verification worksheet from scored candidates CSV.
    
    Args:
        input_csv: Path to deep_scored_candidates_v3.csv
        output_xlsx: Path to output Excel file
        top_n: Number of top candidates to include
    """
    # Read scored candidates
    df = pd.read_csv(input_csv)
    
    # Get top N candidates
    top_candidates = df.head(top_n).copy()
    
    # Create verification columns
    top_candidates['GitHub Profile URL'] = top_candidates['GitHub Username'].apply(
        lambda x: f'https://github.com/{x}'
    )
    
    # Add empty columns for manual work
    top_candidates['Verified LinkedIn URL'] = ''
    top_candidates['LinkedIn Match Quality'] = ''  # Good/Fair/Poor/Not Found
    top_candidates['Notes'] = ''
    
    # Reorder columns for easy verification
    columns = [
        'GitHub Username',
        'Overall Score',
        'Location',
        'GitHub Profile URL',
        'LinkedIn URL',  # Auto-discovered (may be wrong)
        'Verified LinkedIn URL',  # Manual entry
        'LinkedIn Match Quality',
        'Notes',
        'Go_K8s_Operators',
        'IaC_Terraform_Helm',
        'Tooling_Automation',
        'Rationale'
    ]
    
    # Select and reorder columns
    verification_df = top_candidates[columns]
    
    # Write to Excel with formatting
    with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
        verification_df.to_excel(writer, sheet_name='Manual Verification', index=False)
        
        # Get the worksheet
        worksheet = writer.sheets['Manual Verification']
        
        # Set column widths
        worksheet.column_dimensions['A'].width = 20  # GitHub Username
        worksheet.column_dimensions['B'].width = 12  # Score
        worksheet.column_dimensions['C'].width = 20  # Location
        worksheet.column_dimensions['D'].width = 40  # GitHub URL
        worksheet.column_dimensions['E'].width = 40  # Auto LinkedIn
        worksheet.column_dimensions['F'].width = 40  # Verified LinkedIn
        worksheet.column_dimensions['G'].width = 15  # Match Quality
        worksheet.column_dimensions['H'].width = 30  # Notes
        
        # Make header row bold
        for cell in worksheet[1]:
            cell.font = cell.font.copy(bold=True)
    
    print(f"Created manual verification sheet: {output_xlsx}")
    print(f"Top {len(verification_df)} candidates included")
    print(f"\nInstructions:")
    print(f"1. Open {output_xlsx}")
    print(f"2. For each candidate:")
    print(f"   - Click the GitHub Profile URL to view their repos")
    print(f"   - Search LinkedIn for their name + location")
    print(f"   - Verify the LinkedIn profile matches the GitHub profile")
    print(f"   - Enter the correct LinkedIn URL in 'Verified LinkedIn URL'")
    print(f"   - Rate match quality: Good/Fair/Poor/Not Found")
    print(f"   - Add notes if needed")
    print(f"3. Save the file when done")
    print(f"\nFocus on candidates scoring 80+ first (highest priority)")

if __name__ == "__main__":
    # Default paths
    input_csv = Path("output/deep_scored_candidates_v3.csv")
    output_xlsx = Path("output/manual_verification_top_50.xlsx")
    
    # Check if input exists
    if not input_csv.exists():
        print(f"ERROR: Input file not found: {input_csv}")
        print("Run deep_scorer_v3.py first to generate scored candidates.")
        sys.exit(1)
    
    # Create verification sheet
    create_verification_sheet(input_csv, output_xlsx, top_n=50)
