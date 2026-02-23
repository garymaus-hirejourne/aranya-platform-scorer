import os
import sys
import json
from openai import OpenAI
from google import genai
from dotenv import load_dotenv

load_dotenv()


class MultiLLMGenerator:
    """
    Uses both OpenAI GPT-4 and Google Gemini to generate rubrics and search queries.
    Combines insights from both models for better results.
    """
    
    def __init__(self, openai_key=None, gemini_key=None):
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY")
        self.gemini_key = gemini_key or os.getenv("GEMINI_API_KEY")
        
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        if not self.gemini_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        self.openai_client = OpenAI(api_key=self.openai_key)
        self.gemini_client = genai.Client(api_key=self.gemini_key)
    
    def generate_rubric_openai(self, job_description):
        """Generate rubric using OpenAI GPT-4."""
        prompt = f"""You are an expert technical recruiter analyzing a job description.

Job Description:
{job_description}

Create a scoring rubric for evaluating GitHub candidates. The rubric should:
1. Have 5-7 dimensions that matter most for this role
2. Assign point values (total should be 100)
3. Focus on skills visible in GitHub profiles (repos, languages, contributions)

Return ONLY valid JSON in this exact format:
{{
    "rubric": {{
        "Dimension_Name": points,
        "Another_Dimension": points
    }},
    "search_queries": [
        "query 1",
        "query 2"
    ],
    "reasoning": "Brief explanation of rubric design"
}}"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a technical recruiting expert who creates data-driven scoring rubrics."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
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
            result['model'] = 'openai-gpt4'
            return result
            
        except Exception as e:
            print(f"OpenAI error: {e}", file=sys.stderr)
            return None
    
    def generate_rubric_gemini(self, job_description):
        """Generate rubric using Google Gemini."""
        prompt = f"""You are an expert technical recruiter analyzing a job description.

Job Description:
{job_description}

Create a scoring rubric for evaluating GitHub candidates. The rubric should:
1. Have 5-7 dimensions that matter most for this role
2. Assign point values (total should be 100)
3. Focus on skills visible in GitHub profiles (repos, languages, contributions)

Return ONLY valid JSON in this exact format:
{{
    "rubric": {{
        "Dimension_Name": points,
        "Another_Dimension": points
    }},
    "search_queries": [
        "query 1",
        "query 2"
    ],
    "reasoning": "Brief explanation of rubric design"
}}"""

        try:
            response = self.gemini_client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt
            )
            content = response.text.strip()
            
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            result = json.loads(content)
            result['model'] = 'gemini-pro'
            return result
            
        except Exception as e:
            print(f"Gemini error: {e}", file=sys.stderr)
            return None
    
    def ensemble_merge(self, openai_result, gemini_result):
        """
        Merge rubrics from both models using ensemble voting.
        
        Strategy:
        1. Combine all unique dimensions from both models
        2. Average point values where dimensions overlap
        3. Normalize to total 100 points
        4. Combine search queries
        5. Merge reasoning
        """
        if not openai_result or not gemini_result:
            return openai_result or gemini_result
        
        openai_rubric = openai_result.get('rubric', {})
        gemini_rubric = gemini_result.get('rubric', {})
        
        all_dimensions = {}
        
        for dim, points in openai_rubric.items():
            all_dimensions[dim] = {'openai': points, 'gemini': 0, 'count': 1}
        
        for dim, points in gemini_rubric.items():
            if dim in all_dimensions:
                all_dimensions[dim]['gemini'] = points
                all_dimensions[dim]['count'] = 2
            else:
                all_dimensions[dim] = {'openai': 0, 'gemini': points, 'count': 1}
        
        merged_rubric = {}
        for dim, values in all_dimensions.items():
            if values['count'] == 2:
                merged_rubric[dim] = (values['openai'] + values['gemini']) / 2
            else:
                merged_rubric[dim] = values['openai'] or values['gemini']
        
        total_points = sum(merged_rubric.values())
        if total_points > 0:
            normalized_rubric = {
                dim: round((points / total_points) * 100)
                for dim, points in merged_rubric.items()
            }
            
            current_total = sum(normalized_rubric.values())
            if current_total != 100:
                max_dim = max(normalized_rubric.items(), key=lambda x: x[1])
                normalized_rubric[max_dim[0]] += (100 - current_total)
        else:
            normalized_rubric = merged_rubric
        
        openai_queries = set(openai_result.get('search_queries', []))
        gemini_queries = set(gemini_result.get('search_queries', []))
        merged_queries = list(openai_queries | gemini_queries)
        
        merged_reasoning = f"OpenAI: {openai_result.get('reasoning', '')}\n\nGemini: {gemini_result.get('reasoning', '')}"
        
        return {
            'rubric': normalized_rubric,
            'search_queries': merged_queries,
            'reasoning': merged_reasoning,
            'model': 'ensemble',
            'openai_rubric': openai_rubric,
            'gemini_rubric': gemini_rubric,
            'agreement_score': self._calculate_agreement(openai_rubric, gemini_rubric)
        }
    
    def _calculate_agreement(self, rubric1, rubric2):
        """Calculate how much the two models agree (0-1 scale)."""
        common_dims = set(rubric1.keys()) & set(rubric2.keys())
        if not common_dims:
            return 0.0
        
        total_diff = 0
        for dim in common_dims:
            total_diff += abs(rubric1[dim] - rubric2[dim])
        
        max_possible_diff = len(common_dims) * 100
        agreement = 1 - (total_diff / max_possible_diff)
        
        return round(agreement, 2)
    
    def generate_rubric(self, job_description, mode='ensemble'):
        """
        Generate rubric using specified mode.
        
        Args:
            job_description: Text of the job description
            mode: 'openai', 'gemini', or 'ensemble' (default)
        
        Returns:
            dict: Rubric and search queries
        """
        print(f"\n{'='*80}", file=sys.stderr)
        print(f"MULTI-LLM RUBRIC GENERATION (Mode: {mode})", file=sys.stderr)
        print(f"{'='*80}\n", file=sys.stderr)
        
        if mode == 'openai':
            print("Generating rubric with OpenAI GPT-4...", file=sys.stderr)
            return self.generate_rubric_openai(job_description)
        
        elif mode == 'gemini':
            print("Generating rubric with Google Gemini...", file=sys.stderr)
            return self.generate_rubric_gemini(job_description)
        
        else:
            print("Generating rubric with OpenAI GPT-4...", file=sys.stderr)
            openai_result = self.generate_rubric_openai(job_description)
            
            print("Generating rubric with Google Gemini...", file=sys.stderr)
            gemini_result = self.generate_rubric_gemini(job_description)
            
            print("\nMerging results with ensemble voting...", file=sys.stderr)
            ensemble_result = self.ensemble_merge(openai_result, gemini_result)
            
            if ensemble_result:
                print(f"\nModel Agreement Score: {ensemble_result.get('agreement_score', 0):.0%}", file=sys.stderr)
                print(f"{'='*80}\n", file=sys.stderr)
            
            return ensemble_result


def main():
    """Test the multi-LLM generator."""
    if len(sys.argv) < 2:
        print("Usage: python multi_llm_generator.py <job_description_file> [mode]")
        print("  mode: openai, gemini, or ensemble (default)")
        sys.exit(1)
    
    job_desc_file = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else 'ensemble'
    
    with open(job_desc_file, 'r', encoding='utf-8') as f:
        job_description = f.read()
    
    generator = MultiLLMGenerator()
    result = generator.generate_rubric(job_description, mode=mode)
    
    if result:
        print(json.dumps(result, indent=2))
    else:
        print("Failed to generate rubric", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
