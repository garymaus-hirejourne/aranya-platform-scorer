# HireJourne Dashboard Revision Log

## Version 2.3.1 - February 28, 2026

### Changes:
- **Fixed Ngrok webhook integration**
  - Changed `src/app.py` line 266 from `CALLBACK_BASE_URL` to `WEBHOOK_BASE_URL`
  - This fixes environment variable mismatch with launcher script
  - Webhooks now correctly use auto-configured Ngrok URL instead of hardcoded production URL
  - Root cause: Launcher sets `WEBHOOK_BASE_URL`, but app was reading `CALLBACK_BASE_URL`

### Files Modified:
- `src/app.py` - Fixed webhook URL environment variable name

### Verification:
- Completed read-only analysis of Ngrok webhook stability
- Documented findings in `tasks/todo.md`
- Identified and fixed critical environment variable mismatch

---

## Version 2.3 - February 26, 2026

### Changes:
- **Fixed SignalHire enrichment integration**
  - Added POST /enrich endpoint to handle CSV file uploads
  - Integrated with existing `tools/signalhire_enrich.py` script via subprocess
  - Added "LinkedIn Profile" to column name detection in signalhire_enrich.py
  - Fixed storage.py DATA_ROOT path to use relative "data" instead of absolute "/data" (Windows compatibility)
  
- **Dashboard improvements**
  - Added confirmation dialog before starting enrichment ("Are you sure you want to start a new enrichment search?")
  - Updated version display to 2.3
  - Added timestamp display (2/26/2026, 12:53:27 PM)
  - Fixed /status endpoint to return current_run object for progress tracking
  
- **Bug fixes**
  - Fixed Jinja2 template errors in candidate_search.html (using .get() for safe dictionary access)
  - Fixed POST /enrich 405 Method Not Allowed error
  - Added placeholder endpoints for /merge_clay, /merge_clay_candidates, /merge_clay_manual, /download_merged_clay

### Files Modified:
- `src/app.py` - Added POST /enrich endpoint and run_enrichment_process function
- `src/templates/index.html` - Updated version to 2.3, added timestamp
- `src/templates/enrich.html` - Added confirmation dialog JavaScript
- `src/templates/candidate_search.html` - Fixed Jinja2 errors
- `src/lib/storage.py` - Fixed DATA_ROOT path for Windows compatibility
- `tools/signalhire_enrich.py` - Added "LinkedIn Profile" to column detection

### Known Issues:
- Full SignalHire API integration still requires proper webhook handling
- Dashboard progress tracking needs real-time updates from enrichment process

---

## Version 2.2 - February 24, 2026

### Changes:
- Migrated from Flask to FastAPI
- Unified dashboard with multiple tabs (GitHub Sourcing, LinkedIn Discovery, Contact Enrichment, Ngrok Inspector)
- Added static file serving for images
- Implemented basic /status and /batches endpoints

### Files Modified:
- `src/app.py` - Complete rewrite for FastAPI
- `src/templates/index.html` - Unified dashboard layout
- `start_dashboard.bat` - Updated to use uvicorn
- `start_dashboard.ps1` - Updated paths and URL

---

## Version 2.1 and Earlier

See git history for previous changes.
