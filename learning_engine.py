import os
import sys
import json
from openai import OpenAI
from dotenv import load_dotenv
from feedback_tracker import FeedbackTracker
from github import Github

load_dotenv()


class LearningEngine:
    """
    Uses LLM to analyze historical candidate outcomes and improve
    future rubrics and search strategies.
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.client = OpenAI(api_key=self.api_key)
        self.tracker = FeedbackTracker()
        
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            self.github = Github(github_token)
        else:
            self.github = None
    
    def analyze_successful_patterns(self):
        """
        Analyze what made successful candidates stand out.
        
        Returns:
            dict: Insights about successful candidate patterns
        """
        successful = self.tracker.get_successful_candidates('phone_screen')
        
        if len(successful) < 3:
            print("Not enough feedback data yet (need at least 3 successful candidates)", file=sys.stderr)
            return None
        
        print(f"Analyzing {len(successful)} successful candidates...", file=sys.stderr)
        
        candidate_profiles = []
        
        for entry in successful[:20]:
            username = entry['username']
            
            if self.github:
                try:
                    user = self.github.get_user(username)
                    repos = list(user.get_repos(type="owner", sort="updated"))[:10]
                    
                    profile = {
                        'username': username,
                        'outcome': entry['outcome'],
                        'bio': user.bio or "",
                        'location': user.location or "",
                        'followers': user.followers,
                        'repos': [
                            {
                                'name': r.name,
                                'description': r.description or "",
                                'languages': list(r.get_languages().keys()) if not r.private else [],
                                'stars': r.stargazers_count
                            }
                            for r in repos[:5]
                        ]
                    }
                    
                    candidate_profiles.append(profile)
                    
                except Exception as e:
                    print(f"Error fetching {username}: {e}", file=sys.stderr)
        
        if not candidate_profiles:
            print("Could not fetch any candidate profiles from GitHub", file=sys.stderr)
            return None
        
        prompt = f"""You are an expert technical recruiter analyzing successful candidate patterns.

I have data on {len(candidate_profiles)} candidates who were successfully hired or interviewed.

Here are their GitHub profiles:

{json.dumps(candidate_profiles, indent=2)}

Based on these successful candidates, identify:

1. **Common Technologies**: What languages, frameworks, and tools appear most frequently?
2. **Repository Patterns**: What types of projects do they build? (e.g., infrastructure tools, open source contributions, personal projects)
3. **Profile Characteristics**: What bio keywords, locations, or follower counts correlate with success?
4. **Search Query Improvements**: What GitHub search terms would find MORE candidates like these?
5. **Rubric Adjustments**: Should we weight certain technical dimensions higher based on these patterns?

Return your analysis as a JSON object with this structure:
{{
  "common_technologies": ["tech1", "tech2"],
  "repository_patterns": ["pattern1", "pattern2"],
  "profile_characteristics": {{
    "bio_keywords": ["keyword1"],
    "location_patterns": ["pattern1"],
    "follower_threshold": 10
  }},
  "improved_search_queries": [
    "language:go kubernetes followers:>10",
    "terraform infrastructure followers:>5"
  ],
  "rubric_recommendations": [
    {{
      "dimension": "Dimension_Name",
      "current_weight": 20,
      "recommended_weight": 30,
      "reason": "This skill appeared in 80% of successful candidates"
    }}
  ]
}}

Return ONLY the JSON object, no other text."""

        try:
            print("Calling OpenAI to analyze patterns...", file=sys.stderr)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a data-driven technical recruiting analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            insights = json.loads(content)
            
            print("Pattern analysis complete!", file=sys.stderr)
            return insights
            
        except Exception as e:
            print(f"Error analyzing patterns: {e}", file=sys.stderr)
            raise
    
    def refine_rubric(self, original_rubric_data, job_description_text):
        """
        Refine a rubric based on historical learnings.
        
        Args:
            original_rubric_data: The rubric that would normally be generated
            job_description_text: The job description text
        
        Returns:
            dict: Refined rubric with adjusted weights based on learnings
        """
        insights = self.analyze_successful_patterns()
        
        if not insights:
            print("No insights available, using original rubric", file=sys.stderr)
            return original_rubric_data
        
        prompt = f"""You are refining a candidate scoring rubric based on historical hiring data.

Original Rubric (generated from job description):
{json.dumps(original_rubric_data, indent=2)}

Historical Insights (from successful candidates):
{json.dumps(insights, indent=2)}

Job Description:
{job_description_text[:1000]}...

Refine the rubric by:
1. Adjusting dimension weights based on what correlates with successful hires
2. Adding new dimensions if insights reveal important missing skills
3. Updating keywords to match technologies found in successful candidates
4. Ensuring weights still sum to 100

Return the refined rubric in the same JSON format as the original:
{{
  "rubric": [
    {{
      "dimension": "Dimension_Name",
      "weight": 30,
      "max_score": 10,
      "keywords": ["keyword1", "keyword2"],
      "description": "What this measures"
    }}
  ],
  "refinement_notes": "Brief explanation of what changed and why"
}}

Return ONLY the JSON object."""

        try:
            print("Refining rubric based on learnings...", file=sys.stderr)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a technical recruiting expert who optimizes scoring systems."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            refined = json.loads(content)
            
            print(f"Rubric refined: {refined.get('refinement_notes', 'No notes')}", file=sys.stderr)
            
            return refined['rubric']
            
        except Exception as e:
            print(f"Error refining rubric: {e}", file=sys.stderr)
            return original_rubric_data
    
    def optimize_search_queries(self, original_queries):
        """
        Optimize search queries based on what found successful candidates.
        
        Args:
            original_queries: List of search query strings
        
        Returns:
            List of optimized search query strings
        """
        insights = self.analyze_successful_patterns()
        
        if not insights or 'improved_search_queries' not in insights:
            print("No query optimization insights available", file=sys.stderr)
            return original_queries
        
        improved = insights['improved_search_queries']
        
        combined = list(set(original_queries + improved))
        
        print(f"Optimized queries: {len(original_queries)} -> {len(combined)}", file=sys.stderr)
        
        return combined


if __name__ == "__main__":
    engine = LearningEngine()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'analyze':
        insights = engine.analyze_successful_patterns()
        if insights:
            print(json.dumps(insights, indent=2))
    else:
        print("Usage: python learning_engine.py analyze")
        print("\nThis will analyze successful candidate patterns from feedback data.")
