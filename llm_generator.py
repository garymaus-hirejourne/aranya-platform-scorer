import os
import sys
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class RubricGenerator:
    """
    Uses OpenAI to generate a scoring rubric and GitHub search queries
    from a job description.
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def generate_rubric_and_queries(self, job_description_text):
        """
        Generate a scoring rubric and GitHub search queries from a JD.
        
        Args:
            job_description_text: Full text of the job description
            
        Returns:
            dict: {
                'rubric': [{'dimension': str, 'weight': int, 'max_score': int, 
                           'keywords': [str], 'description': str}],
                'search_queries': [str]
            }
        """
        
        prompt = f"""You are an expert technical recruiter analyzing a job description to create a GitHub-based candidate scoring system.

Job Description:
{job_description_text}

Based on this job description, generate:

1. A scoring rubric with 5-7 technical dimensions that can be evaluated from GitHub profiles
2. GitHub search query keywords to find relevant candidates

For the rubric, each dimension should have:
- dimension: A short name (e.g., "Go_K8s_Operators", "IaC_Terraform")
- weight: Importance percentage (all weights should sum to 100)
- max_score: Maximum points (typically 10)
- keywords: List of GitHub keywords/technologies to look for in repos (languages, frameworks, tools)
- description: Brief explanation of what this dimension measures

For search queries, provide 3-5 GitHub search query strings that combine:
- Relevant programming languages (e.g., "language:go")
- Key technologies (e.g., "kubernetes", "terraform")
- Follower thresholds to ensure quality (e.g., "followers:>5")

Return your response as a JSON object with this exact structure:
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
  "search_queries": [
    "language:go language:python followers:>5",
    "kubernetes terraform followers:>10"
  ]
}}

IMPORTANT: Return ONLY the JSON object, no other text."""

        try:
            print("Calling OpenAI API to generate rubric and queries...", file=sys.stderr)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a technical recruiting expert who creates GitHub-based candidate scoring systems."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
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
            
            result = json.loads(content)
            
            total_weight = sum(dim['weight'] for dim in result['rubric'])
            if abs(total_weight - 100) > 1:
                print(f"WARNING: Rubric weights sum to {total_weight}, not 100. Normalizing...", file=sys.stderr)
                for dim in result['rubric']:
                    dim['weight'] = round((dim['weight'] / total_weight) * 100, 1)
            
            print(f"Generated rubric with {len(result['rubric'])} dimensions", file=sys.stderr)
            print(f"Generated {len(result['search_queries'])} search queries", file=sys.stderr)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"Error parsing OpenAI response as JSON: {e}", file=sys.stderr)
            print(f"Raw response: {content}", file=sys.stderr)
            raise
        except Exception as e:
            print(f"Error calling OpenAI API: {e}", file=sys.stderr)
            raise
    
    def rubric_to_csv(self, rubric_data, output_path):
        """
        Convert rubric JSON to CSV format matching the existing rubric structure.
        
        Args:
            rubric_data: List of rubric dimension dicts
            output_path: Path to save CSV file
        """
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            writer.writerow(['Dimension', 'Weight (%)', 'Max Score', 'Evidence Examples', 'Scoring Guidelines'])
            
            for dim in rubric_data:
                evidence = '; '.join(dim['keywords'])
                guidelines = dim['description']
                
                writer.writerow([
                    dim['dimension'],
                    dim['weight'],
                    dim['max_score'],
                    evidence,
                    guidelines
                ])
        
        print(f"Rubric saved to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python llm_generator.py <job_description_text_file>", file=sys.stderr)
        sys.exit(1)
    
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        jd_text = f.read()
    
    generator = RubricGenerator()
    result = generator.generate_rubric_and_queries(jd_text)
    
    print(json.dumps(result, indent=2))
