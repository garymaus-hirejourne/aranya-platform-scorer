# Aranya Platform Scorer

Intelligence-led sourcing, enrichment, and rubric-based scoring for elite **Platform Engineer** candidates — aligned with the JetStream Manifesto philosophy.

This repository powers automated outbound pipelines at **HireJourne** for identifying, enriching, and ranking top-tier platform engineering talent (Kubernetes, ArgoCD, Go, observability, GitOps-native infrastructure, etc.).

## Project Overview

We believe outbound dealmaking (and talent sourcing) is broken — slow, manual, and disconnected from data.

This tool changes that.

**Aranya Platform Scorer** is an intelligence engine that:
- Hunts GitHub contributors and profiles matching elite platform engineering signals
- Enriches candidates via SignalHire (verified emails, LinkedIn overlays, company data)
- Applies structured rubric scoring
- Outputs ranked results for cold outreach sequences

No more manual spreadsheet grinding or intern search queries. We build what others outsource.

**JetStream Alignment**  
> "Code Is Capital. Custom scrapers, verified email enrichment, LinkedIn overlays, all automated."

## Core Features

- **SignalHire Integration** — API client for bulk enrichment and callback handling
- **Email & Outreach Automation** — Library for sending cold emails with personalized payloads
- **Data Persistence** — CSV/JSONL writers for results and merged outputs
- **Modular Scoring** — Extensible person/model logic for platform engineer rubrics
- **Tools & Scripts** — Standalone enrichment runner and result merger

## Repository Structure
aranya-platform-scorer/
├── src/                    # Core application code
│   ├── app.py              # Main entry point / orchestration
│   ├── lib/                # Shared utilities
│   │   ├── csv_writer.py
│   │   ├── emailer.py
│   │   └── storage.py
│   ├── models/             # Data models & callbacks
│   │   └── person_callback.py
│   ├── services/           # External integrations
│   │   └── signalhire_client.py
│   └── init.py
├── tools/                  # Standalone scripts & helpers
│   ├── merge_results.py    # Combine & deduplicate outputs
│   └── signalhire_enrich.py # Run enrichment jobs
├── output/                 # Results (gitignored by default)
├── .dockerignore
├── .env.example            # Template for API keys, endpoints, etc.
├── .gitignore
├── .python-version
└── README.md               # This file

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/garymaus-hirejourne/aranya-platform-scorer.git
   cd aranya-platform-scorer
2. Powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1    # Windows
   # or
   source .venv/bin/activate       # macOS/Linux
3. Install dependencies
   (Create requirements.txt if missing — see below)
  **Bash
   pip install -r requirements.txt
4. Configure environment
   Copy .env.example → .env and fill in:
   SignalHire API key
   SMTP/email settings
   Any other endpoints/secrets

5. Run enrichment example
  **Bash
   python tools/signalhire_enrich.py
   # or your main orchestration script
   python src/app.py
   
Outputs land in output/ (CSV + JSONL).
