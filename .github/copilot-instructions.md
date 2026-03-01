# HireJourne Unified Dashboard - Developer Guide

## Project Overview

**HireJourne Platform** is a veteran-owned business connecting military veterans to elite platform engineering roles through intelligent automation. The unified dashboard provides a complete 4-step talent acquisition pipeline from GitHub discovery to verified contact enrichment.

**Mission**: Connect veterans to platform engineering roles through automation excellence, data integrity, and quality-over-quantity candidate sourcing.

**Architecture**: Unified FastAPI dashboard with 4-step workflow:
1. **GitHub Sourcing & Deep Scoring** - Discover elite engineers from open-source contributions
2. **LinkedIn Discovery** - Enrich with LinkedIn profile data (Clay.com integration)
3. **Contact Enrichment** - Find verified emails/phones via SignalHire API
4. **Ngrok Inspector** - Monitor webhook traffic in real-time

## Unified Dashboard Architecture & Data Flow

### Step 1 & 2: GitHub Sourcing & Deep Scoring

```
[Job Description PDF]
    ↓
[pdf_parser.py] → Extract requirements, generate rubric via Gemini API
    ↓
[deep_scorer_v3.py] → Search GitHub for relevant contributors
    ↓
[Scoring Engine] → Rate candidates against rubric dimensions
    ↓
[linkedin_extractor.py] → Extract LinkedIn URLs (only if explicitly found)
    ↓
[Output CSV] → output/deep_scored_candidates_v3.csv
```

### Step 3: LinkedIn Discovery (Clay.com)

```
[deep_scored_candidates_v3.csv]
    ↓
[Manual Clay.com workflow] → Enrich with LinkedIn profile data
    ↓
[Download from Clay.com] → clay_enriched_results.csv
    ↓
[merge_clay_results.py] → Merge back with scored candidates
```

### Step 4: Contact Enrichment (SignalHire)

```
[LinkedIn URLs CSV]
    ↓
[FastAPI POST /enrich] → Upload CSV, create batch
    ↓
[tools/signalhire_enrich.py] → Submit to SignalHire API in batches
    ↓
[Webhook /callback] → Receive enriched candidate data
    ↓
[Flatten & Store] → Append to data/batches/{batch_id}/results.csv
    ↓
[Dashboard Progress] → Real-time status updates via polling
```

## Key Components

| Component | Location | Purpose | Step |
|-----------|----------|---------|------|
| **Unified Dashboard** | `src/app.py` | FastAPI server with multi-tab interface | All |
| **Deep Scorer** | `deep_scorer_v3.py` | GitHub sourcing with AI-generated rubrics | 1-2 |
| **PDF Parser** | `pdf_parser.py` | Extract job requirements from PDFs | 1-2 |
| **LinkedIn Extractor** | `linkedin_extractor.py` | Extract LinkedIn URLs from GitHub profiles | 1-2 |
| **Clay Enrichment** | `clay_enrichment.py` | Clay.com API integration (manual workflow) | 3 |
| **SignalHire Script** | `tools/signalhire_enrich.py` | Standalone enrichment script | 4 |
| **SignalHire Client** | `src/services/signalhire_client.py` | Async HTTP client for Person API | 4 |
| **Storage Layer** | `src/lib/storage.py` | File-based batch tracking & persistence | 4 |
| **CSV Flattening** | `src/lib/csv_writer.py` | Expand nested JSON to flat CSV rows | 4 |
| **Email Sender** | `src/lib/emailer.py` | Send result CSVs via Gmail | 4 |
| **Merge Tool** | `merge_clay_results.py` | Join Clay results with scored candidates | 3 |

## Critical Workflows

### Running the Unified Dashboard

```bash
# Start dashboard (Windows)
start_dashboard.bat

# This launches:
# 1. FastAPI server on port 8080
# 2. Ngrok tunnel for webhooks
# 3. Browser at http://127.0.0.1:8080/

# Dashboard provides 4 tabs:
# - Dashboard: Real-time status and progress tracking
# - Step 1 & 2: GitHub Sourcing (upload job PDFs, run scoring)
# - Step 3: LinkedIn Discovery (Clay.com integration)
# - Step 4: Contact Enrichment (SignalHire upload)
# - Ngrok Inspector: Webhook traffic monitoring
```

### Step 1 & 2: GitHub Sourcing with AI Rubrics

```bash
# Requires GITHUB_TOKEN and GEMINI_API_KEY in .env
python deep_scorer_v3.py

# Process:
# 1. Reads job description PDF from rubric_samples/
# 2. Generates scoring rubric via Gemini API
# 3. Searches GitHub for relevant contributors
# 4. Scores candidates against rubric dimensions
# 5. Extracts LinkedIn URLs (only if explicitly found on GitHub)
# 6. Outputs: output/deep_scored_candidates_v3.csv
```

**Key Features:**
- AI-generated rubrics from job descriptions
- Dynamic GitHub repository selection based on job requirements
- LinkedIn URL extraction (explicit only - no auto-generation)
- Dimension-based scoring with weighted criteria
- Location filtering and deduplication

### Step 4: SignalHire Enrichment Lifecycle

1. **Upload CSV** → `new_batch_id()` creates timestamp ID (e.g., `20260207_123456`)
2. **Submit Phase** → Loop over identifiers (LinkedIn URLs, emails), call SignalHire Person API, collect `request_id` values
3. **Mapping** → Store `request_id → batch_id` in `REQUESTS_DIR` for webhook correlation
4. **Webhook Callback** → SignalHire POSTs enriched data to `/callback` with `Request-Id` header
5. **Flatten & Persist** → `flatten_callback_payload()` expands to one row per contact (email, phone)
6. **Completion** → When all pending requests resolved, send results.csv to user email, mark batch status "complete"

### CSV Flattening Strategy

SignalHire returns nested candidate objects. `flatten_callback_payload()` creates **one row per contact type**:

```
uid='abc123', full_name='Alice', status='found', linkedin_url='...', contact_type='email', contact_value='alice@example.com'
uid='abc123', full_name='Alice', status='found', linkedin_url='...', contact_type='phone', contact_value='555-1234'
```

If no contacts found → emit single row with contact fields as `None`.

## Configuration & Environment

### Required for GitHub Scoring (Step 1-2)
- `GITHUB_TOKEN` – GitHub Personal Access Token (read public repos)
- `GEMINI_API_KEY` – Google Gemini API key for rubric generation

### Required for SignalHire Enrichment (Step 4)
- `SIGNALHIRE_API_KEY` – SignalHire Person API key
- `CALLBACK_BASE_URL` – Public webhook URL (ngrok or production domain)
- `SIGNALHIRE_API_BASE_URL` (default: `https://www.signalhire.com`)
- `SIGNALHIRE_API_PREFIX` (default: `/api/v1`)

### Optional
- `DATA_ROOT` (default: `data` - relative path for Windows compatibility)
- `GMAIL_USER`, `GMAIL_APP_PASSWORD` – For sending enriched results
- `CLAY_API_KEY` – Clay.com API key (if using automated Clay integration)

See `.env.example` for template.

## File Organization & Storage

```
aranya-platform-scorer/
├── src/
│   ├── app.py                    # FastAPI unified dashboard
│   ├── templates/                # Jinja2 HTML templates
│   │   ├── index.html           # Main dashboard
│   │   ├── candidate_search.html # Step 1-2 tab
│   │   ├── linkedin_discovery.html # Step 3 tab
│   │   └── enrich.html          # Step 4 tab
│   ├── lib/
│   │   ├── storage.py           # Batch tracking & persistence
│   │   ├── emailer.py           # Result notification
│   │   └── csv_writer.py        # CSV flattening utilities
│   └── services/
│       └── signalhire_client.py # SignalHire API client
├── tools/
│   └── signalhire_enrich.py     # Standalone enrichment script
├── output/                       # Generated CSVs (gitignored)
│   ├── deep_scored_candidates_v3.csv
│   └── clay_enriched_results.csv
├── data/batches/{batch_id}/      # SignalHire batch tracking
│   ├── status.json              # Batch status and progress
│   ├── results.csv              # Flattened enrichment results
│   └── results.json             # Raw SignalHire payloads
├── data/requests/
│   └── {request_id}.txt         # Request ID to batch ID mapping
├── logs/                         # Server logs
│   ├── server_*.log
│   └── server_*.err.log
├── uploads/                      # User-uploaded CSVs
├── deep_scorer_v3.py            # Main GitHub scoring script
├── linkedin_extractor.py        # LinkedIn URL extraction
├── pdf_parser.py                # Job description parsing
├── start_dashboard.bat          # Windows startup script
├── REVISION_LOG.md              # Change tracking
└── .env                         # API keys & config (gitignored)
```

## Common Tasks & Commands

### Running the Dashboard
```bash
# Windows: Use batch file
start_dashboard.bat

# Manual start (if needed)
python -m uvicorn src.app:app --host 0.0.0.0 --port 8080
ngrok http 8080

# Dashboard opens at http://127.0.0.1:8080/
```

### Running GitHub Scoring (Step 1-2)
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables in .env
GITHUB_TOKEN=ghp_xxxxx
GEMINI_API_KEY=xxxxx

# Run scoring
python deep_scorer_v3.py

# Output: output/deep_scored_candidates_v3.csv
```

### Running SignalHire Enrichment (Step 4)
```bash
# Via dashboard: Upload CSV on Step 4 tab
# Or direct script:
python tools/signalhire_enrich.py "path/to/input.csv" [batch_size]

# Requires SIGNALHIRE_API_KEY and CALLBACK_BASE_URL in .env
```

### Checking Batch Status
```bash
curl "http://localhost:8000/status/{batch_id}"
curl "http://localhost:8000/credits"  # SignalHire remaining credits
```

### Merging Results
```bash
# Join enrichment CSV back into original input
python tools/merge_results.py input.csv results.csv output.csv [linkedin_column_name]
```

## Code Patterns & Conventions

### Async/Await
- `src/app.py` uses async FastAPI handlers
- `signalhire_client.submit_identifier()` is async (httpx.AsyncClient)
- Email sending wraps sync SMTP in `asyncio.to_thread()` to avoid blocking

### GitHub Scoring
- `deep_scorer_v3.py` uses AI-generated rubrics from job descriptions
- Dynamic repository selection based on job requirements
- Contribution filtering: configurable thresholds
- Location filtering: keyword matching on GitHub profiles
- LinkedIn URL extraction: only if explicitly found (no auto-generation)
- Dimensions scored based on rubric criteria with weighted importance

### Error Handling
- **GitHub errors** → Logged to stderr, batch continues to next repo
- **SignalHire errors** → Return `{ success: False, error: str, diagnostics: {...} }`
- **Callback errors** → Logged to batch status `errors[]`, user notified via email
- **Missing data** → Emit rows anyway (e.g., candidate without contacts still creates 1 row)

### Status Tracking Format
```json
{
  "status": "processing|complete",
  "email": "user@example.com",
  "total_items": 10,
  "pending": ["request-id-1", "request-id-2"],
  "received": 8,
  "errors": [{ "item": "url", "error": "reason" }],
  "submissions": [{ "item": "url", "success": true, "request_id": "...", "diagnostics": {...} }]
}
```

## Gotchas & Debugging Tips

1. **GitHub API Rate Limits** – 60 req/hour unauthenticated, 5000/hour with token. Batch repos to stay under.
2. **Location Filtering Fuzzy** – Keyword matching on location strings; some contributors may report non-standard regions.
3. **Request-Id Header Sensitivity** – SignalHire webhook lookup depends on exact case. Code handles both `Request-Id` and `Request-ID`.
4. **SignalHire Rate Limits** – HTTP 429 → slow down submissions; consider `time.sleep(0.25)` between batches.
5. **CSV Column Variations** – `merge_results.py` searches by multiple LinkedIn column names to be flexible.
6. **Nested Contact Expansion** – Each contact type creates separate CSV row. Deduplication must happen downstream.
7. **File-Based Storage** – No concurrent batch writes; scales poorly in high-concurrency scenarios.

## Key Files for Quick Reference

- **Unified Dashboard**: [src/app.py](src/app.py)
- **GitHub Scoring**: [deep_scorer_v3.py](deep_scorer_v3.py)
- **PDF Parser**: [pdf_parser.py](pdf_parser.py)
- **LinkedIn Extractor**: [linkedin_extractor.py](linkedin_extractor.py)
- **SignalHire Script**: [tools/signalhire_enrich.py](tools/signalhire_enrich.py)
- **SignalHire Client**: [src/services/signalhire_client.py](src/services/signalhire_client.py)
- **Storage/Batching**: [src/lib/storage.py](src/lib/storage.py)
- **CSV Transformation**: [src/lib/csv_writer.py](src/lib/csv_writer.py)
- **Clay Enrichment**: [clay_enrichment.py](clay_enrichment.py)
- **Merge Tool**: [merge_clay_results.py](merge_clay_results.py)
- **Revision Log**: [REVISION_LOG.md](REVISION_LOG.md)

## HireJourne Mission & Values

**Veteran-Owned Business**: HireJourne is committed to serving the military community by connecting veterans to elite platform engineering roles.

**Core Values**:
1. **Veterans First** - Prioritize veteran-owned business operations and veteran candidate sourcing
2. **Quality Over Quantity** - Focus on elite platform engineers with proven open-source contributions
3. **Automation Excellence** - Minimize manual work through intelligent workflows
4. **Data Integrity** - Ensure accurate LinkedIn URLs, contact information, and scoring metrics
5. **Simplicity** - Keep the codebase maintainable and workflows straightforward

## Current Status (v2.3 - Feb 26, 2026)
- ✅ Unified dashboard with 4-step workflow tabs
- ✅ GitHub scoring with AI-generated rubrics
- ✅ LinkedIn URL extraction (explicit only)
- ✅ SignalHire enrichment integration
- ✅ Webhook callback handling
- ✅ Batch progress tracking
- ✅ Windows compatibility (relative paths)
- ⚠️ Clay.com integration (manual workflow)
- ⚠️ Real-time progress updates (polling-based)

