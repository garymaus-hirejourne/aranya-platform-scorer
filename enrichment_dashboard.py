import os
import csv
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file
import pandas as pd

app = Flask(__name__, static_folder='graphics', static_url_path='/graphics')


class EnrichmentManager:
    """Manages CSV file detection and merging for contact enrichment."""
    
    def __init__(self, output_dir="output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def get_available_csvs(self):
        """
        Get all CSV files from output directory with metadata.
        Returns list sorted by modification time (newest first).
        """
        csv_files = []
        
        for csv_path in self.output_dir.glob("*.csv"):
            try:
                stat = csv_path.stat()
                
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    headers = next(reader, [])
                    row_count = sum(1 for _ in reader)
                
                file_type = self._classify_csv(csv_path.name, headers)
                
                csv_files.append({
                    'filename': csv_path.name,
                    'path': str(csv_path),
                    'size_kb': round(stat.st_size / 1024, 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'modified_timestamp': stat.st_mtime,
                    'row_count': row_count,
                    'columns': len(headers),
                    'headers': headers[:10],
                    'file_type': file_type
                })
            except Exception as e:
                print(f"Error reading {csv_path}: {e}")
                continue
        
        csv_files.sort(key=lambda x: x['modified_timestamp'], reverse=True)
        
        return csv_files
    
    def _classify_csv(self, filename, headers):
        """Classify CSV type based on filename and headers."""
        filename_lower = filename.lower()
        headers_lower = [h.lower() for h in headers]
        
        if 'final_candidates' in filename_lower or 'scored' in filename_lower:
            return 'scored_candidates'
        elif 'enriched' in filename_lower or 'clay' in filename_lower:
            return 'enrichment_results'
        elif any('email' in h or 'phone' in h for h in headers_lower):
            return 'enrichment_results'
        elif any('score' in h or 'weighted' in h for h in headers_lower):
            return 'scored_candidates'
        else:
            return 'unknown'
    
    def get_latest_by_type(self):
        """Get the most recent file of each type."""
        all_files = self.get_available_csvs()
        
        latest = {
            'scored_candidates': None,
            'enrichment_results': None
        }
        
        for file_info in all_files:
            file_type = file_info['file_type']
            if file_type in latest and latest[file_type] is None:
                latest[file_type] = file_info
        
        return latest
    
    def merge_csvs(self, scored_path, enriched_path, output_filename=None):
        """
        Merge scored candidates CSV with enrichment results CSV.
        
        Args:
            scored_path: Path to scored candidates CSV
            enriched_path: Path to enrichment results CSV
            output_filename: Optional output filename
        
        Returns:
            Path to merged CSV
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"merged_candidates_{timestamp}.csv"
        
        output_path = self.output_dir / output_filename
        
        df_scored = pd.read_csv(scored_path)
        df_enriched = pd.read_csv(enriched_path)
        
        merge_key = self._find_merge_key(df_scored, df_enriched)
        
        if not merge_key:
            raise ValueError("Could not find common column to merge on")
        
        merged = df_scored.merge(
            df_enriched,
            on=merge_key,
            how='left',
            suffixes=('', '_enriched')
        )
        
        if 'email_enriched' in merged.columns and 'email' in merged.columns:
            merged['email'] = merged['email'].fillna(merged['email_enriched'])
            merged = merged.drop(columns=['email_enriched'])
        
        if 'phone_enriched' in merged.columns and 'phone' in merged.columns:
            merged['phone'] = merged['phone'].fillna(merged['phone_enriched'])
            merged = merged.drop(columns=['phone_enriched'])
        
        merged.to_csv(output_path, index=False)
        
        return str(output_path)
    
    def _find_merge_key(self, df1, df2):
        """Find common column to merge on."""
        common_cols = set(df1.columns) & set(df2.columns)
        
        priority_keys = ['username', 'github_username', 'linkedin_url', 'LinkedIn URL', 'email']
        
        for key in priority_keys:
            if key in common_cols:
                return key
        
        if common_cols:
            return list(common_cols)[0]
        
        return None


manager = EnrichmentManager()


@app.route('/')
def index():
    """Main enrichment control panel."""
    return render_template('enrichment.html')


@app.route('/api/files')
def api_files():
    """Get all available CSV files."""
    files = manager.get_available_csvs()
    return jsonify(files)


@app.route('/api/latest')
def api_latest():
    """Get latest files by type."""
    latest = manager.get_latest_by_type()
    return jsonify(latest)


@app.route('/api/merge', methods=['POST'])
def api_merge():
    """Merge two CSV files."""
    data = request.json
    
    scored_path = data.get('scored_path')
    enriched_path = data.get('enriched_path')
    output_filename = data.get('output_filename')
    
    if not scored_path or not enriched_path:
        return jsonify({'error': 'Missing required paths'}), 400
    
    try:
        output_path = manager.merge_csvs(scored_path, enriched_path, output_filename)
        return jsonify({
            'success': True,
            'output_path': output_path,
            'message': f'Successfully merged to {Path(output_path).name}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<filename>')
def api_download(filename):
    """Download a CSV file."""
    file_path = manager.output_dir / filename
    
    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(str(file_path), as_attachment=True, download_name=filename)


if __name__ == '__main__':
    print("\n" + "="*80)
    print("CONTACT ENRICHMENT CONTROL PANEL")
    print("="*80)
    print("\nStarting enrichment dashboard...")
    print("Open your browser to: http://localhost:5001")
    print("\nThis dashboard helps you:")
    print("  - View all CSV files in output/")
    print("  - Identify scored candidates vs enrichment results")
    print("  - Merge rubric scores with Clay enrichment data")
    print("\nPress Ctrl+C to stop the server")
    print("="*80 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
