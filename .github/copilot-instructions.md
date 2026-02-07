# Copilot Instructions for Aranya Platform Scorer

## Project Overview

**Aranya Platform Scorer** is a two-stage talent acquisition automation pipeline for sourcing and ranking elite **Platform Engineer** candidates.

**Stage 1 – GitHub Sourcing**: Scans major platform engineering repositories (Argo CD, Kubernetes, Cilium, etc.) to identify top contributors and rank them by a rubric.

**Stage 2 – SignalHire Enrichment**: Enriches ranked candidates with verified contact information (emails, phones) via SignalHire API.

## Two-Stage Architecture & Data Flow

### Stage 1: GitHub Sourcing (aranya_scorer.py)

```
[GitHub Public Repos]
    ↓
[aranya_scorer.py] → Query top contributors via GitHub API
    ↓
[Scoring Rubric] → Rate on Operators, GitOps, Storage, Networking, Observability, IaC, etc.
    ↓
[Output CSV] → GitHub username, overall score, commits, location, dimension scores
```

### Stage 2: SignalHire Enrichment (app.py / FastAPI)

```
[Candidate CSV/LinkedIn URLs]
    ↓
[FastAPI /upload] → Create batch, parse identifiers
    ↓
[SignalHire Person API] → Submit for enrichment
    ↓
[Webhook /callback] → Receive enriched candidate data
    ↓
[Flatten & Store] → Append to results.csv + results.json
    ↓
[Email Results] → Send CSV to user when batch complete
```

## Key Components

| Component | Location | Purpose | Stage |
|-----------|----------|---------|-------|
| **GitHub Scorer** | `src/aranya_scorer.py` | Scan repos, extract contributors, apply rubric | 1 |
| **FastAPI App** | `src/app.py` | Webhook server for batch enrichment | 2 |
| **SignalHire Client** | `src/services/signalhire_client.py` | Async HTTP client for Person API | 2 |
| **Storage Layer** | `src/lib/storage.py` | File-based batch tracking & persistence | 2 |
| **CSV Flattening** | `src/lib/csv_writer.py` | Expand nested JSON to flat CSV rows | 2 |
| **Email Sender** | `src/lib/emailer.py` | Send result CSVs via Gmail | 2 |
| **Merge Tool** | `tools/merge_results.py` | Join enrichment results to original CSV | Both |

## Critical Workflows

### Stage 1: Running GitHub Sourcing

```bash
# Requires GITHUB_TOKEN in .env
python src/aranya_scorer.py > candidates.csv 2> candidates.log

# Output: CSV with columns:
# GitHub Username, Overall Score, Commits, Repo, Location, 
# Operators, GitOps, Storage, Networking, MultiCluster, IaC, 
# Observability, OSS, Product, Rationale, Risks
```

**Repos Scanned:**
- argoproj/argo-cd (GitOps focus)
- kubernetes/kubernetes (Operators, MultiCluster)
- cilium/cilium (Networking)
- rook/rook, ceph/ceph-csi-operator (Storage)
- operator-framework/operator-sdk (Operators, IaC)
- prometheus-operator/prometheus-operator (Observability)

**Filters:**
- Min 10 commits per contributor
- Top 50 per repo
- Deduplicated across repos
- US/SFO location preferred

**Scoring Rubric:**
Profile dimensions weighted 5–20 points. Boost logic:
- Argo repos: +5 GitOps bonus if 200+ commits, +5 Operators bonus
- Kubernetes: +8 Operators, +5 MultiCluster
- Cilium: +8 Networking, +5 Observability
- Storage repos: +8 Storage dimension
- Zero dimensions randomized 0–(rubric_max/3)

### Stage 2: Batch Enrichment Lifecycle

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

### Stage 1 Required
- `GITHUB_TOKEN` – GitHub Personal Access Token (read public repos)

### Stage 2 Required (for production)
- `SIGNALHIRE_API_KEY` – SignalHire Person API key
- `SIGNALHIRE_API_BASE_URL` (default: `https://www.signalhire.com`)
- `SIGNALHIRE_API_PREFIX` (default: `/api/v1`)
- `CALLBACK_BASE_URL` – Public webhook host (e.g., production domain or ngrok)
- `GMAIL_USER`, `GMAIL_APP_PASSWORD` – For sending enriched results
- `DATA_ROOT` (default: `./data` for local, `/data` for production)

See `.env.example` for template.

## File Organization & Storage

```
./data/batches/{batch_id}/
  ├── original.csv        # User's uploaded CSV
  ├── status.json         # { pending: [], received: N, errors: [...] }
  ├── results.csv         # Flattened enrichment results (appended per callback)
  └── results.json        # Raw SignalHire payloads keyed by request_id

./data/requests/
  └── {request_id}.txt    # Single-line file containing batch_id
```

## Common Tasks & Commands

### Running Stage 1: GitHub Sourcing
```bash
# Install deps
pip install -r requirements.txt

# Set GITHUB_TOKEN in .env
export GITHUB_TOKEN=ghp_xxxxx

# Run sourcing
python src/aranya_scorer.py > candidates.csv 2> score.log

# Output will be CSV sorted by Overall Score descending
```

### Running Stage 2: Enrichment Service
```bash
# Start FastAPI server
python -m uvicorn src.app:app --host 0.0.0.0 --port 8000

# Visit http://localhost:8000 for web form
# Upload CSV and user email → batch starts enrichment
# When complete, results.csv sent to email
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
- `aranya_scorer.py` scans hardcoded `REPOS_TO_SCAN` list
- Contribution filtering: `MIN_COMMITS=10`, `TOP_N_PER_REPO=50`
- Location filtering: US/SFO preferred via keyword matching
- Dimensions scored min 0, max rubric[dim], with boosted ranges per repo

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

- **GitHub Sourcing**: [src/aranya_scorer.py](src/aranya_scorer.py)
- **Enrichment App**: [src/app.py](src/app.py)
- **SignalHire Client**: [src/services/signalhire_client.py](src/services/signalhire_client.py)
- **Storage/Batching**: [src/lib/storage.py](src/lib/storage.py)
- **CSV Transformation**: [src/lib/csv_writer.py](src/lib/csv_writer.py)
- **Data Models**: [src/models/person_callback.py](src/models/person_callback.py)

