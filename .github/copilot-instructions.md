# Copilot Instructions for Aranya Platform Scorer

## Project Overview

**Aranya Platform Scorer** is a FastAPI-based talent enrichment service that automates sourcing and ranking of platform engineering candidates. It integrates with **SignalHire** (third-party enrichment API) to verify emails, extract contact info, and compile CSV results for outreach.

## Architecture & Data Flow

```
User CSV (LinkedIn URLs)
    ↓
[FastAPI /upload] → Create batch, parse URLs
    ↓
[SignalHire Client] → Submit each URL to Person API
    ↓
[SignalHire Webhook] → /callback receives enriched candidate data
    ↓
[Storage] → Append to batch results.csv + results.json
    ↓
[All complete?] → Email results.csv to user, update batch status
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Entry Point** | `src/app.py` | FastAPI endpoints: `/upload`, `/callback`, `/status/{batch_id}`, `/download/{batch_id}`, `/health`, `/credits` |
| **SignalHire Integration** | `src/services/signalhire_client.py` | Async HTTP client submitting identifiers to SignalHire Person API |
| **Storage Layer** | `src/lib/storage.py` | File-based persistence: batch tracking, request↔batch mapping, status JSON |
| **Data Flattening** | `src/lib/csv_writer.py` | Transforms nested JSON callback payloads into flat CSV rows |
| **Notifications** | `src/lib/emailer.py` | Sends result CSVs and error notifications via Gmail |
| **Standalone Tools** | `tools/signalhire_enrich.py` | CLI for bulk submission (legacy endpoint: `/candidate/search`) |
|  | `tools/merge_results.py` | Joins enrichment results back into original CSV |

## Critical Workflows & Patterns

### Batch Processing Lifecycle

1. **Upload CSV** → `new_batch_id()` creates timestamp-based ID (e.g., `12345678`)
2. **Submit Phase** → Loop over URLs, call `submit_identifier(url, callback_url)`, collect `request_id` values
3. **Mapping** → Store `request_id → batch_id` in `REQUESTS_DIR` for callback lookup
4. **Callback Handling** → Incoming webhook contains `Request-Id` header; find batch, append results
5. **Completion** → When all pending requests resolved (empty pending list), send email → mark `status: "complete"`

### Request–Batch Correlation

```python
# Submission flow
request_id = submit_identifier(url)
storage.map_request_to_batch(request_id, batch_id)
status["pending"].append(request_id)

# Callback flow
request_id = request.headers.get("Request-Id")
batch_id = storage.find_batch_by_request(request_id)
if request_id in status["pending"]:
    pending.remove(request_id)
# If pending is empty → complete batch
```

### CSV Flattening Strategy

SignalHire returns nested candidate objects with **multiple contacts per person** (email, phone, LinkedIn, etc.). `flatten_callback_payload()` expands to one CSV row **per contact**:

```
uid='abc123', full_name='Alice', status='found', linkedin_url='...', contact_type='email', contact_value='alice@example.com'
uid='abc123', full_name='Alice', status='found', linkedin_url='...', contact_type='phone', contact_value='555-1234'
```

If no contacts → emit single row with `contact_*` fields as `None`.

## Configuration & Environment

Required env vars:
- `SIGNALHIRE_API_KEY` – API key for SignalHire service
- `SIGNALHIRE_API_BASE_URL` (default: `https://www.signalhire.com`)
- `SIGNALHIRE_API_PREFIX` (default: `/api/v1`)
- `CALLBACK_BASE_URL` – Public webhook host for callbacks (e.g., production domain)
- `GMAIL_USER`, `GMAIL_APP_PASSWORD` – For sending result emails
- `DATA_ROOT` (default: `/data`) – Root for batch and request storage

See `.env.example` for template.

## File Organization & Storage

```
/data/batches/{batch_id}/
  ├── original.csv        # User's uploaded CSV
  ├── status.json         # { pending: [], received: N, errors: [...] }
  ├── results.csv         # Flattened enrichment results (appended per callback)
  └── results.json        # Raw SignalHire payloads keyed by request_id

/data/requests/
  └── {request_id}.txt    # Single-line text file containing batch_id
```

## Common Tasks & Commands

### Running the Service
```bash
# Requires Python 3.9+, FastAPI, httpx
pip install -r requirements.txt
python -m uvicorn src.app:app --host 0.0.0.0 --port 8000
```

### Using Standalone Tools

**Bulk Enrichment** (submit batches of identifiers):
```bash
python tools/signalhire_enrich.py input.csv [batch_size=100]
```

**Merge Results** (join enrichment CSV back to original input):
```bash
python tools/merge_results.py input.csv enrichment_results.csv output.csv [linkedin_column_name]
```

### Checking Batch Status
```bash
curl "http://localhost:8000/status/{batch_id}"
curl "http://localhost:8000/credits"  # Check remaining SignalHire API credits
```

## Code Patterns & Conventions

### Async/Await
- `src/app.py` uses async FastAPI handlers
- `signalhire_client.submit_identifier()` is async (httpx.AsyncClient)
- Email sending wraps sync SMTP in `asyncio.to_thread()` to avoid blocking

### Error Handling
- **API Errors** → Return `{ success: False, error: str, diagnostics: {...} }`
- **Callback Errors** → Log to batch status `errors[]`, send error email if batch_id found
- **Missing Data** → Emit rows anyway (e.g., candidate without contacts still creates 1 row)

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

1. **Request-Id Header Sensitivity** – Callback lookup depends on exact `Request-Id` header case. Code handles both `Request-Id` and `Request-ID`.
2. **SignalHire Rate Limits** – HTTP 429 → slow down batch submissions; `tools/signalhire_enrich.py` includes `time.sleep(0.25)`.
3. **CSV Column Variations** – `merge_results.py` searches by multiple LinkedIn column names (`linkedin`, `LinkedIn URL`, `linkedin_url`, `profile`).
4. **Nested Contact Expansion** – Each contact type (email, phone) creates a separate CSV row. Deduplication/pivoting must happen downstream.
5. **File-Based Storage Limitations** – No concurrent batch writes; file-based lookup is O(1) but scales poorly if used as append-only log in high-concurrency scenarios.

## Key Files for Quick Reference

- **Main orchestration**: [src/app.py](src/app.py)
- **SignalHire API client**: [src/services/signalhire_client.py](src/services/signalhire_client.py)
- **Storage/batching logic**: [src/lib/storage.py](src/lib/storage.py)
- **CSV transformation**: [src/lib/csv_writer.py](src/lib/csv_writer.py)
- **Data models**: [src/models/person_callback.py](src/models/person_callback.py)
