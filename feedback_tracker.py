import csv
import json
import os
from pathlib import Path
from datetime import datetime


class FeedbackTracker:
    """
    Tracks candidate outcomes to enable learning and improvement.
    """
    
    def __init__(self, feedback_db_path="data/candidate_feedback.jsonl"):
        self.feedback_db_path = Path(feedback_db_path)
        self.feedback_db_path.parent.mkdir(exist_ok=True)
        
        if not self.feedback_db_path.exists():
            self.feedback_db_path.touch()
    
    def add_feedback(self, username, outcome, notes="", job_description_hash=None, rubric_used=None):
        """
        Record feedback for a candidate.
        
        Args:
            username: GitHub username
            outcome: One of: 'hired', 'interviewed', 'phone_screen', 'rejected', 'no_response'
            notes: Optional notes about why this outcome occurred
            job_description_hash: Hash/ID of the JD used to find this candidate
            rubric_used: The rubric dimensions/weights used
        """
        feedback_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'username': username,
            'outcome': outcome,
            'notes': notes,
            'job_description_hash': job_description_hash,
            'rubric_used': rubric_used
        }
        
        with open(self.feedback_db_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(feedback_entry) + '\n')
        
        print(f"Feedback recorded: {username} -> {outcome}")
    
    def get_all_feedback(self):
        """
        Retrieve all feedback entries.
        
        Returns:
            List of feedback dicts
        """
        if not self.feedback_db_path.exists():
            return []
        
        feedback = []
        with open(self.feedback_db_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    feedback.append(json.loads(line))
        
        return feedback
    
    def get_successful_candidates(self, min_outcome_level='phone_screen'):
        """
        Get candidates who reached a certain outcome level.
        
        Args:
            min_outcome_level: Minimum success level
                - 'hired' (highest)
                - 'interviewed'
                - 'phone_screen'
                - 'no_response' (lowest, not considered success)
        
        Returns:
            List of successful candidate feedback entries
        """
        outcome_hierarchy = {
            'hired': 4,
            'interviewed': 3,
            'phone_screen': 2,
            'no_response': 1,
            'rejected': 0
        }
        
        min_level = outcome_hierarchy.get(min_outcome_level, 2)
        
        all_feedback = self.get_all_feedback()
        successful = [
            f for f in all_feedback 
            if outcome_hierarchy.get(f['outcome'], 0) >= min_level
        ]
        
        return successful
    
    def get_statistics(self):
        """
        Get aggregate statistics on candidate outcomes.
        
        Returns:
            Dict with outcome counts and success rate
        """
        all_feedback = self.get_all_feedback()
        
        if not all_feedback:
            return {'total': 0, 'outcomes': {}, 'success_rate': 0.0}
        
        outcomes = {}
        for entry in all_feedback:
            outcome = entry['outcome']
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
        
        successful = len(self.get_successful_candidates('phone_screen'))
        success_rate = (successful / len(all_feedback)) * 100 if all_feedback else 0
        
        return {
            'total': len(all_feedback),
            'outcomes': outcomes,
            'success_rate': round(success_rate, 2)
        }


def import_feedback_from_csv(csv_path, outcome_column='outcome', username_column='username'):
    """
    Bulk import feedback from a CSV file.
    
    Args:
        csv_path: Path to CSV with candidate outcomes
        outcome_column: Name of column containing outcome
        username_column: Name of column containing GitHub username
    """
    tracker = FeedbackTracker()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            username = row.get(username_column)
            outcome = row.get(outcome_column)
            
            if username and outcome:
                tracker.add_feedback(
                    username=username,
                    outcome=outcome.lower(),
                    notes=row.get('notes', '')
                )
    
    print(f"Imported feedback from {csv_path}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python feedback_tracker.py add <username> <outcome> [notes]")
        print("  python feedback_tracker.py stats")
        print("  python feedback_tracker.py import <csv_path>")
        print("\nOutcomes: hired, interviewed, phone_screen, rejected, no_response")
        sys.exit(1)
    
    command = sys.argv[1]
    tracker = FeedbackTracker()
    
    if command == 'add':
        username = sys.argv[2]
        outcome = sys.argv[3]
        notes = sys.argv[4] if len(sys.argv) > 4 else ""
        tracker.add_feedback(username, outcome, notes)
    
    elif command == 'stats':
        stats = tracker.get_statistics()
        print(json.dumps(stats, indent=2))
    
    elif command == 'import':
        csv_path = sys.argv[2]
        import_feedback_from_csv(csv_path)
    
    else:
        print(f"Unknown command: {command}")
