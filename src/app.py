#!/usr/bin/env python3
from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

import os
import csv
import json
import asyncio
from pathlib import Path
from typing import Any, List
import httpx

from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import dashboard data logic
from dashboard import DashboardData

from .lib import storage
from .lib.emailer import send_result_email, send_error_email
from .services.signalhire_client import submit_identifier, API_BASE, API_PREFIX, API_KEY
from .lib.csv_writer import flatten_callback_payload

APP_NAME = "SignalHire Cloud Webhook"


app = FastAPI(title=APP_NAME, version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="src/templates")

# Initialize Dashboard Data
dashboard_data = DashboardData()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "version": "2.2",
        "stats": dashboard_data.get_feedback_stats(),
        "history": dashboard_data.get_pipeline_history()
    })

@app.get("/candidate-search", response_class=HTMLResponse)
async def candidate_search(request: Request):
    return templates.TemplateResponse("candidate_search.html", {
        "request": request,
        "status": {},
        "default_rubrics": {},
        "job_profiles": []
    })

@app.get("/linkedin-discovery", response_class=HTMLResponse)
async def linkedin_discovery(request: Request):
    return templates.TemplateResponse("linkedin_discovery.html", {"request": request})

@app.get("/enrich", response_class=HTMLResponse)
async def enrich_get(request: Request):
    return templates.TemplateResponse("enrich.html", {"request": request, "result": None})

@app.post("/enrich", response_class=HTMLResponse)
async def enrich_post(
    request: Request,
    input_file: UploadFile = File(None),
    input_csv: str = Form(""),
    webhook_base: str = Form(""),
    api_key: str = Form(""),
    batch_size: int = Form(50),
    timeout: int = Form(900),
    poll_interval: int = Form(20)
):
    """Handle SignalHire enrichment form submission."""
    try:
        # Determine input source
        input_path = None
        if input_file and input_file.filename:
            # Save uploaded file
            upload_dir = Path("uploads")
            upload_dir.mkdir(exist_ok=True)
            input_path = upload_dir / input_file.filename
            content = await input_file.read()
            with open(input_path, "wb") as f:
                f.write(content)
        elif input_csv:
            input_path = Path(input_csv)
            if not input_path.exists():
                raise ValueError(f"Input CSV path does not exist: {input_csv}")
        else:
            raise ValueError("No input file or path provided")
        
        # Create run status for Dashboard tracking
        batch_id = storage.new_batch_id()
        run_status = {
            "batch_id": batch_id,
            "stage": "running_enrichment",
            "input": str(input_path),
            "output_final": "",
            "started_at": datetime.now().isoformat(),
            "batch_size": batch_size,
            "timeout": timeout,
            "poll_interval": poll_interval
        }
        
        # Save initial status
        storage.write_status(batch_id, run_status)
        
        # Start enrichment process asynchronously
        asyncio.create_task(run_enrichment_process(
            batch_id=batch_id,
            input_path=input_path,
            webhook_base=webhook_base,
            api_key=api_key,
            batch_size=batch_size,
            timeout=timeout
        ))
        
        # Return success response
        result = {
            "ok": True,
            "input": str(input_path),
            "output": f"Enrichment started. Batch ID: {batch_id}",
            "count_in": 0,
            "count_out": 0,
            "batch_id": batch_id
        }
        return templates.TemplateResponse("enrich.html", {"request": request, "result": result})
    except Exception as e:
        result = {
            "ok": False,
            "error": str(e),
            "input": "",
            "output": "",
            "count_in": 0,
            "count_out": 0
        }
        return templates.TemplateResponse("enrich.html", {"request": request, "result": result})


@app.get("/api/scorer/start")
async def start_scorer():
    """Start the deep scorer in the background."""
    # Run deep_scorer_v3.py asynchronously
    process = await asyncio.create_subprocess_shell(
        'python deep_scorer_v3.py output/sharded_users.csv',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    return {"status": "started", "message": "Deep scorer started in background. This may take 20-30 minutes."}

@app.post("/api/clay/export")
async def export_clay():
    """Run export_for_clay.py and return the CSV."""
    process = await asyncio.create_subprocess_shell(
        'python export_for_clay.py',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
    
    file_path = Path("output/clay_upload_candidates.csv")
    if file_path.exists():
        return FileResponse(path=file_path, filename="clay_upload_candidates.csv", media_type="text/csv")
    raise HTTPException(status_code=404, detail="Export failed or file not found")

@app.post("/api/clay/merge")
async def merge_clay(clay_file: UploadFile = File(...)):
    """Accept enriched Clay CSV, save it, run merge_clay_results.py, and return final CSV."""
    # Save the uploaded file
    clay_path = Path("output/clay_enriched_results.csv")
    content = await clay_file.read()
    with open(clay_path, "wb") as f:
        f.write(content)
        
    # Run merge script
    process = await asyncio.create_subprocess_shell(
        'python merge_clay_results.py',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
    
    # Return merged file
    final_path = Path("output/deep_scored_candidates_v3_enriched.csv")
    if final_path.exists():
        return FileResponse(path=final_path, filename="deep_scored_candidates_v3_enriched.csv", media_type="text/csv")
    raise HTTPException(status_code=500, detail="Merge process failed")
@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "healthy", "service": APP_NAME}


@app.get("/credits")
async def credits() -> JSONResponse:
    """Proxy to SignalHire credits endpoint using configured API key.

    Returns JSON with remaining credits or an error with diagnostics.
    """
    try:
        if not API_KEY:
            raise HTTPException(status_code=500, detail="Missing SIGNALHIRE_API_KEY")
        url = f"{API_BASE}{API_PREFIX}/credits?withoutContacts=true"
        headers = {"apikey": API_KEY}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=headers)
            try:
                data = resp.json()
            except Exception:
                raw = await resp.aread()
                data = {"raw": raw[:1024].decode(errors="ignore")}
            return JSONResponse(
                {
                    "ok": resp.status_code in range(200, 300),
                    "status_code": resp.status_code,
                    "headers": {k: v for k, v in resp.headers.items() if k.lower() in {"content-type"}},
                    "data": data,
                },
                status_code=resp.status_code,
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload(csv_file: UploadFile = File(...), user_email: str = Form(...)) -> JSONResponse:
    """Accept CSV of LinkedIn URLs and user email, create batch, submit Person API requests."""
    try:
        content = await csv_file.read()
        # Create batch and persist original CSV
        batch_id = storage.new_batch_id()
        storage.save_original_csv(batch_id, content)

        # Parse LinkedIn URLs (single-column CSV)
        urls: List[str] = []
        for row in csv.reader(content.decode("utf-8-sig").splitlines()):
            if not row:
                continue
            url = (row[0] or "").strip()
            if url and url.lower().startswith("http"):
                urls.append(url)
        if not urls:
            raise HTTPException(status_code=400, detail="No LinkedIn URLs found in CSV")

        # Initialize status
        status = {
            "status": "processing",
            "email": user_email,
            "total_items": len(urls),
            "pending": [],
            "received": 0,
            "errors": [],
            "submissions": [],  # per-item diagnostics
        }

        # Submit identifiers to SignalHire Person API with callbackUrl
        callback_base = os.getenv(
            "WEBHOOK_BASE_URL",
            "https://webhook--signalhire-webhook--jgdqh2mydks5.code.run",
        ).rstrip("/")
        callback_url = f"{callback_base}/signalhire/callback"

        for url in urls:
            resp = await submit_identifier(url, callback_url)
            # record diagnostics for visibility
            status["submissions"].append({
                "item": url,
                "success": resp.get("success"),
                "request_id": resp.get("request_id"),
                "error": resp.get("error"),
                "diagnostics": resp.get("diagnostics"),
            })
            if not resp["success"]:
                status["errors"].append({"item": url, "error": resp.get("error")})
                continue
            rid = resp.get("request_id")
            if rid:
                storage.map_request_to_batch(rid, batch_id)
                status["pending"].append(rid)

        storage.write_status(batch_id, status)
        return JSONResponse({
            "status": "accepted",
            "batch_id": batch_id,
            "submitted": len(status["pending"]),
            "errors": len(status["errors"]),
            "callback_url": callback_url,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/signalhire/callback")
async def callback(request: Request) -> JSONResponse:
    """Handle SignalHire Person API callback, append JSON/CSV, and manage batch status and email."""
    try:
        request_id = request.headers.get("Request-Id") or request.headers.get("Request-ID")
        if not request_id:
            raise HTTPException(status_code=400, detail="Missing Request-Id header")

        payload = await request.json()
        # Lookup batch
        batch_id = storage.find_batch_by_request(request_id)
        if not batch_id:
            # Accept but log unknown request id
            return JSONResponse({"status": "accepted", "warning": "unknown request id"})

        # Append raw JSON per request
        storage.append_results_json(batch_id, request_id, payload)

        # Flatten and append CSV rows
        rows = flatten_callback_payload(payload)
        storage.append_results_csv(batch_id, rows)

        # Update status: remove pending id, increment received
        status = storage.read_status(batch_id)
        pending = status.get("pending", [])
        if request_id in pending:
            pending.remove(request_id)
        status["pending"] = pending
        status["received"] = int(status.get("received", 0)) + 1

        # If no pending, mark complete and send email
        if not pending:
            status["status"] = "complete"
            storage.write_status(batch_id, status)
            try:
                # Email results.csv
                csv_path = storage.batch_csv_path(batch_id)
                user_email = status.get("email")
                if user_email and csv_path.exists():
                    await send_result_email(user_email, batch_id, csv_path)
            except Exception as email_err:
                # Record email error but do not fail webhook
                status.setdefault("errors", []).append({"email_error": str(email_err)})
                storage.write_status(batch_id, status)
        else:
            # Save interim status
            storage.write_status(batch_id, status)

        return JSONResponse({"status": "accepted", "batch_id": batch_id})
    except HTTPException:
        raise
    except Exception as e:
        # Try to notify user on error if possible
        try:
            # If we can derive a batch, send error email
            req_id = request.headers.get("Request-Id") or ""
            batch_id = storage.find_batch_by_request(req_id) if req_id else None
            if batch_id:
                st = storage.read_status(batch_id)
                st.setdefault("errors", []).append({"callback_error": str(e)})
                storage.write_status(batch_id, st)
                user_email = st.get("email")
                if user_email:
                    await send_error_email(user_email, batch_id, str(e))
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))


async def run_enrichment_process(
    batch_id: str,
    input_path: Path,
    webhook_base: str,
    api_key: str,
    batch_size: int,
    timeout: int
):
    """Run SignalHire enrichment process asynchronously using existing script."""
    try:
        # Update status
        status = storage.read_status(batch_id) or {}
        status["stage"] = "running_enrichment"
        storage.write_status(batch_id, status)
        
        # Run the existing signalhire_enrich.py script
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        process = await asyncio.create_subprocess_shell(
            f'python tools/signalhire_enrich.py "{input_path}" {batch_size}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=project_root
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            output_text = stdout.decode('utf-8')
            status["stage"] = "waiting_for_callbacks"
            status["output"] = output_text
            
            # Parse requestId from output and save mapping
            # Output format: "Submitted batch; response: {\"requestId\":127555019}"
            import re
            import json
            request_ids = []
            for match in re.finditer(r'response:\s*(\{[^}]+\})', output_text):
                try:
                    response_json = json.loads(match.group(1))
                    request_id = response_json.get("requestId")
                    if request_id:
                        request_ids.append(str(request_id))
                        storage.map_request_to_batch(str(request_id), batch_id)
                except Exception:
                    pass
            
            status["pending"] = request_ids
            status["received"] = 0
        else:
            status["stage"] = "error"
            status["error"] = stderr.decode('utf-8')
        
        storage.write_status(batch_id, status)
        
    except Exception as e:
        status = storage.read_status(batch_id) or {}
        status["stage"] = "error"
        status["error"] = str(e)
        storage.write_status(batch_id, status)

from datetime import datetime

@app.get("/status")
async def get_status() -> JSONResponse:
    """Get webhook server status and statistics"""
    try:
        # Calculate records
        total_records = 0
        run_records = 0
        
        batches_dir = Path("data/batches")
        if batches_dir.exists():
            for batch_dir in batches_dir.iterdir():
                if batch_dir.is_dir() and (batch_dir / "status.json").exists():
                    st = storage.read_status(batch_dir.name)
                    if st:
                        total_records += st.get("received", 0)
                        
                        # Just a simple heuristic for "current run" vs "lifetime"
                        # For now we'll just set run_records to the most recent batch
                        run_records = st.get("received", 0)
        
        # Find current run (most recent batch) and auto-timeout stuck batches
        current_run = None
        if batches_dir.exists():
            batches = []
            for batch_dir in batches_dir.iterdir():
                if batch_dir.is_dir() and (batch_dir / "status.json").exists():
                    st = storage.read_status(batch_dir.name)
                    if st:
                        # Auto-timeout stuck batches (default timeout: 900 seconds = 15 minutes)
                        if st.get("stage") in ["running_enrichment", "waiting_for_callbacks"]:
                            started_at = st.get("started_at", "")
                            timeout_seconds = st.get("timeout", 900)
                            try:
                                from datetime import datetime
                                start_time = datetime.fromisoformat(started_at)
                                elapsed = (datetime.now() - start_time).total_seconds()
                                if elapsed > timeout_seconds:
                                    # Auto-timeout this batch
                                    st["stage"] = "error_timeout"
                                    st["error"] = f"Auto-timed out after {int(elapsed)}s (timeout: {timeout_seconds}s)"
                                    storage.write_status(batch_dir.name, st)
                            except Exception:
                                pass  # If timestamp parsing fails, skip timeout check
                        batches.append(st)
            
            # Sort by timestamp and get most recent
            if batches:
                batches.sort(key=lambda x: x.get("started_at", ""), reverse=True)
                latest = batches[0]
                if latest.get("stage") in ["running_enrichment", "waiting_for_callbacks"]:
                    current_run = latest
        
        stats = {
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "main_file_exists": True,
            "lifetime_total_records": total_records,
            "run_file_records": run_records,
            "run_file_successful": run_records,
            "run_file_failed": 0,
            "current_run": current_run
        }
        return JSONResponse(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/batches")
async def list_batches() -> JSONResponse:
    """List all available batch files"""
    try:
        batches_dir = Path("data/batches")
        if not batches_dir.exists():
            return JSONResponse([])
            
        batches = []
        for batch_dir in batches_dir.iterdir():
            if batch_dir.is_dir() and (batch_dir / "status.json").exists():
                st = storage.read_status(batch_dir.name)
                if st:
                    batches.append({
                        "batch_id": batch_dir.name,
                        "stage": st.get("stage", "unknown"),
                        "started_at": st.get("started_at", "unknown"),
                        "input": st.get("input", ""),
                        "batch_size": st.get("batch_size", 0)
                    })
        
        # Sort by started_at descending
        batches.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        return JSONResponse(batches)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{batch_id}")
async def status(batch_id: str) -> JSONResponse:
    st = storage.read_status(batch_id)
    if not st:
        raise HTTPException(status_code=404, detail="Unknown batch id")
    return JSONResponse(st)


@app.get("/download/{batch_id}")
async def download(batch_id: str) -> FileResponse:
    csv_path = storage.batch_csv_path(batch_id)
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="results.csv not found for batch")
    return FileResponse(str(csv_path), media_type="text/csv", filename=f"results_{batch_id}.csv")

@app.post("/merge_clay")
async def merge_clay_endpoint() -> JSONResponse:
    """Merge enriched data with Clay export."""
    return JSONResponse({"ok": False, "error": "Clay merge endpoint not yet implemented"})

@app.get("/merge_clay_candidates")
async def merge_clay_candidates_endpoint(folder: str = "") -> JSONResponse:
    """List available files for Clay merging."""
    return JSONResponse({"ok": False, "error": "Clay candidates listing not yet implemented"})

@app.post("/merge_clay_manual")
async def merge_clay_manual_endpoint() -> JSONResponse:
    """Manual Clay merge operation."""
    return JSONResponse({"ok": False, "error": "Manual Clay merge not yet implemented"})

@app.get("/download_merged_clay")
async def download_merged_clay() -> FileResponse:
    """Download merged Clay CSV."""
    raise HTTPException(status_code=404, detail="Merged Clay file not available")
