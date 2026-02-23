import os
import json
import time
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify
from feedback_tracker import FeedbackTracker
from learning_engine import LearningEngine

app = Flask(__name__)


class DashboardData:
    """Aggregates data for the dashboard visualization."""
    
    def __init__(self):
        self.tracker = FeedbackTracker()
        self.learning_engine = None
        try:
            self.learning_engine = LearningEngine()
        except:
            pass
    
    def get_feedback_stats(self):
        """Get candidate feedback statistics."""
        return self.tracker.get_statistics()
    
    def get_feedback_timeline(self):
        """Get feedback entries over time."""
        all_feedback = self.tracker.get_all_feedback()
        
        timeline = []
        for entry in sorted(all_feedback, key=lambda x: x['timestamp']):
            timeline.append({
                'timestamp': entry['timestamp'],
                'username': entry['username'],
                'outcome': entry['outcome'],
                'notes': entry.get('notes', '')
            })
        
        return timeline
    
    def get_learning_insights(self):
        """Get current learning insights if available."""
        if not self.learning_engine:
            return None
        
        stats = self.tracker.get_statistics()
        if stats['total'] < 3:
            return {'status': 'insufficient_data', 'message': f"Need 3+ candidates, have {stats['total']}"}
        
        try:
            insights = self.learning_engine.analyze_successful_patterns()
            return insights
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_pipeline_history(self):
        """Get history of pipeline runs from output files."""
        output_dir = Path('output')
        if not output_dir.exists():
            return []
        
        runs = []
        
        for rubric_file in sorted(output_dir.glob('generated_rubric_*.csv'), reverse=True):
            timestamp_str = rubric_file.stem.replace('generated_rubric_', '')
            
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                
                queries_file = output_dir / f'generated_queries_{timestamp_str}.json'
                candidates_file = output_dir / f'final_candidates_{timestamp_str}.csv'
                
                run_info = {
                    'timestamp': timestamp.isoformat(),
                    'rubric_file': str(rubric_file),
                    'has_queries': queries_file.exists(),
                    'has_candidates': candidates_file.exists()
                }
                
                if queries_file.exists():
                    with open(queries_file, 'r') as f:
                        queries_data = json.load(f)
                        run_info['num_queries'] = len(queries_data.get('search_queries', []))
                        run_info['num_dimensions'] = len(queries_data.get('rubric', []))
                
                if candidates_file.exists():
                    with open(candidates_file, 'r') as f:
                        num_candidates = sum(1 for line in f) - 1
                        run_info['num_candidates'] = num_candidates
                
                runs.append(run_info)
            except:
                continue
        
        return runs[:10]
    
    def get_rubric_evolution(self):
        """Track how rubric weights have changed over time."""
        output_dir = Path('output')
        if not output_dir.exists():
            return []
        
        evolution = []
        
        for queries_file in sorted(output_dir.glob('generated_queries_*.json')):
            timestamp_str = queries_file.stem.replace('generated_queries_', '')
            
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                
                with open(queries_file, 'r') as f:
                    data = json.load(f)
                    rubric = data.get('rubric', [])
                    
                    weights = {dim['dimension']: dim['weight'] for dim in rubric}
                    
                    evolution.append({
                        'timestamp': timestamp.isoformat(),
                        'weights': weights
                    })
            except:
                continue
        
        return evolution


dashboard_data = DashboardData()


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/stats')
def api_stats():
    """Get overall statistics."""
    return jsonify(dashboard_data.get_feedback_stats())


@app.route('/api/timeline')
def api_timeline():
    """Get feedback timeline."""
    return jsonify(dashboard_data.get_feedback_timeline())


@app.route('/api/insights')
def api_insights():
    """Get learning insights."""
    insights = dashboard_data.get_learning_insights()
    return jsonify(insights or {})


@app.route('/api/pipeline_history')
def api_pipeline_history():
    """Get pipeline run history."""
    return jsonify(dashboard_data.get_pipeline_history())


@app.route('/api/rubric_evolution')
def api_rubric_evolution():
    """Get rubric weight evolution over time."""
    return jsonify(dashboard_data.get_rubric_evolution())


@app.route('/api/progress')
def api_progress():
    """Get current pipeline progress (if running)."""
    progress_file = Path('output/pipeline_progress.json')
    
    if progress_file.exists():
        try:
            with open(progress_file, 'r') as f:
                return jsonify(json.load(f))
        except:
            pass
    
    return jsonify({'status': 'idle'})


if __name__ == '__main__':
    print("\n" + "="*80)
    print("RECRUITING PIPELINE DASHBOARD")
    print("="*80)
    print("\nStarting dashboard server...")
    print("Open your browser to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("="*80 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
