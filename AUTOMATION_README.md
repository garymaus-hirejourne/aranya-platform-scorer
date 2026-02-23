# Automated Recruiting Pipeline

## Overview

This automation pipeline eliminates manual work from your candidate sourcing process. Simply provide a job description PDF, and the system will:

1. **Extract** the job requirements from the PDF
2. **Generate** a custom scoring rubric and GitHub search queries using OpenAI
3. **Search** GitHub deeply (bypassing the 1000-result limit) for matching candidates
4. **Score** all candidates against the generated rubric
5. **Output** the top 100-200 profiles ready for enrichment in Clay

## Prerequisites

1. **API Keys** (already configured in `.env`):
   - `GITHUB_TOKEN` - For GitHub API access
   - `OPENAI_API_KEY` - For LLM-based rubric generation

2. **Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### Basic Usage

```bash
python orchestrator.py path/to/job_description.pdf
```

This will output the top 200 candidates by default.

### Custom Number of Candidates

```bash
python orchestrator.py path/to/job_description.pdf --top 150
```

## What Happens During Execution

### Step 1: PDF Parsing
The system extracts all text from your job description PDF.

### Step 2: LLM Generation
OpenAI GPT-4 analyzes the job description and creates:
- A **scoring rubric** with 5-7 technical dimensions (e.g., "Go_K8s_Operators", "IaC_Terraform")
- **GitHub search queries** optimized to find candidates with relevant skills

### Step 3: Deep Search
The system runs a "sharded" GitHub search that:
- Breaks searches into smaller chunks (by US state and year)
- Bypasses the 1000-result API limit
- Finds thousands of potential candidates
- Handles rate limiting automatically

**Note**: This step can take 1-3 hours depending on query breadth.

### Step 4: Scoring
Each candidate's GitHub profile is evaluated:
- Public repositories are analyzed for relevant technologies
- Scores are assigned across all rubric dimensions
- Weighted total score is calculated
- Risk flags are added (e.g., "Potential Non-US Resident")

**Note**: This step can take 30-60 minutes for large candidate pools.

### Step 5: Output
The top N candidates are saved to a timestamped CSV file ready for Clay enrichment.

## Output Files

All outputs are saved to the `output/` directory with timestamps:

- `generated_rubric_YYYYMMDD_HHMMSS.csv` - The scoring rubric used
- `generated_queries_YYYYMMDD_HHMMSS.json` - The search queries and full LLM output
- `final_candidates_YYYYMMDD_HHMMSS.csv` - **Your final candidate list for Clay**

## CSV Format for Clay

The final candidates CSV includes:

| Column | Description |
|--------|-------------|
| `username` | GitHub username |
| `location` | User's location (if provided) |
| `bio` | User's bio |
| `followers` | Number of GitHub followers |
| `public_repos` | Number of public repositories |
| `score_*` | Individual dimension scores |
| `weighted_score` | Overall score (0-10 scale) |
| `risks` | Any risk flags (e.g., non-US resident) |

## Example Workflow

1. **Prepare your job description** as a PDF
2. **Run the pipeline**:
   ```bash
   python orchestrator.py job_descriptions/platform_engineer.pdf --top 200
   ```
3. **Wait** for completion (1-4 hours total)
4. **Upload** `output/final_candidates_YYYYMMDD_HHMMSS.csv` to Clay
5. **Enrich** the profiles using Clay's LinkedIn/email lookup

## Monitoring Progress

The script outputs detailed progress to stderr:
- `[STEP X/5]` - Current pipeline stage
- `[SHARD SEARCH]` - Search progress and user counts
- `[SCORER]` - Scoring progress
- `[RATE LIMIT]` - Automatic rate limit handling

You can redirect stderr to a log file:
```bash
python orchestrator.py job.pdf 2> pipeline.log
```

## Rate Limits

The system automatically handles GitHub API rate limits:
- **Search API**: 30 requests/minute
- **Core API**: 5000 requests/hour

When limits are hit, the script will sleep and resume automatically.

## Customization

### Modify Search Strategy

Edit `orchestrator.py` function `run_shard_search()`:
- Change `US_STATES` to target different regions
- Adjust `YEARS` range for different account ages
- Modify follower thresholds in queries

### Adjust Scoring Logic

Edit `orchestrator.py` function `run_deep_scorer()`:
- Change keyword matching logic
- Adjust score increments
- Modify risk detection keywords

### Use Different LLM Model

Edit `llm_generator.py` line 72:
```python
model="gpt-4o",  # Change to "gpt-4-turbo" or "gpt-3.5-turbo"
```

## Troubleshooting

### "MISSING TOKEN" Error
Ensure `.env` file exists in the project root with valid API keys.

### Rate Limit Issues
The script handles this automatically. If you see frequent rate limits, the search may be too broad.

### No Candidates Found
Check `generated_queries_*.json` to see what search terms were used. The job description may need more specific technical details.

### Unicode Errors on Windows
These are cosmetic console output errors. The CSV files are saved correctly with UTF-8 encoding.

## Architecture

```
orchestrator.py          # Main pipeline controller
├── pdf_parser.py        # Extracts text from PDF
├── llm_generator.py     # Generates rubric + queries via OpenAI
├── run_shard_search()   # Deep GitHub user search
└── run_deep_scorer()    # Scores users against rubric
```

## Next Steps

After getting your candidate CSV:
1. Upload to Clay
2. Enrich with LinkedIn profiles
3. Enrich with email addresses
4. Export to your ATS or outreach tool

---

**Questions?** Check the main project README or review the code comments in each module.
