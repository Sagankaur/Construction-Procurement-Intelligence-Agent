# SiteSage AI

SiteSage AI is a local construction procurement intelligence prototype for the Kaya AI IIT India Hackathon 2026. It helps project managers detect material delays, vendor reliability risks, purchase order follow-ups, and schedule-impacting procurement bottlenecks.

## Problem Statement

Construction teams often track hundreds of purchase orders across emails, contracts, spreadsheets, and vendor calls. A delayed critical material such as structural steel, MEP cable, or a generator package can block site progress before the project team has a clear warning.

## Solution

SiteSage AI combines document upload, cited retrieval, delay prediction, vendor scoring, and alert generation in one Streamlit dashboard. It is intentionally lightweight so it can run locally on a Windows laptop during a hackathon demo.

## Features

- Upload PDF, TXT, CSV, Markdown, and Excel procurement documents.
- Ask procurement questions using a RAG flow with cited document chunks.
- Fall back to deterministic cited answers if Ollama is unavailable.
- Predict delivery delay risk with scikit-learn and synthetic procurement history.
- Score vendor reliability from delivery, quality, and communication signals.
- Generate alerts for high-risk deliveries, vendor escalation, and schedule impact.
- Display charts and actionable tables in a Streamlit dashboard.

## Architecture

```text
Streamlit UI
  -> pages/01_Overview.py
  -> pages/02_Upload_Documents.py
  -> pages/03_Ask_AI_Agent.py
  -> pages/04_Delay_Prediction.py
  -> pages/05_Vendor_Risk.py
  -> pages/06_Alerts.py

Backend
  -> src/document_loader.py  SQLite chunks + FAISS retrieval
  -> src/rag_engine.py       Ollama prompt + cited fallback answers
  -> src/delay_model.py      scikit-learn delay risk model
  -> src/vendor_risk.py      vendor reliability scoring
  -> src/alerts.py           procurement alert generation
  -> src/schedule_impact.py  phase float / critical-path heuristic
  -> src/database.py         SQLite setup and helpers
```

Scheduling terms (promised delivery, ROJ, expected delay, schedule impact): see `doc_for_team/procurement_scheduling_glossary.md`.

## Tech Stack

- Python
- Streamlit
- Pandas and NumPy
- Scikit-learn
- FAISS CPU
- SQLite
- Plotly
- Ollama for optional local LLM inference

Recommended local models:

- `qwen2.5:7b`
- `gemma3:4b`
- `llama3.1:8b` if performance allows

## Setup

```powershell
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Optional Ollama setup for local LLM inference:

```powershell
ollama serve
ollama pull qwen2.5:7b
$env:OLLAMA_MODEL="qwen2.5:7b"
$env:SITESAGE_USE_OLLAMA="1"
```

If Ollama is not installed or not running, SiteSage still returns cited extractive answers from indexed documents.

See [docs/ollama_setup.md](docs/ollama_setup.md) for the full local setup flow and presentation notes.

## Run Locally

```powershell
..\.venv\Scripts\python.exe -m streamlit run app.py
```

Open `http://localhost:8501`.

## Demo Workflow

1. Open the app and review the Overview dashboard.
2. Go to Upload Documents and click `Load Sample Documents`.
3. Ask one of the demo questions in Ask AI Agent.
4. Open Delay Prediction and score a structural steel delivery.
5. Review Vendor Risk for high-risk vendors such as ABC Metals.
6. Open Alerts to show critical procurement actions.

Demo questions:

- Which deliveries are at risk this month?
- Which vendors are high risk?
- What purchase orders need follow-up?
- What materials are delayed?
- What is the expected ROJ date for steel?
- Which critical materials may affect the project schedule?

## Kaya AI Hackathon Alignment

Kaya's Amber concept learns project context and helps teams make decisions. SiteSage follows that pattern for procurement: it learns from uploaded project documents, retrieves cited context, predicts delivery risk, ranks vendors, and turns risk into project-manager-ready alerts.

## Verification

```powershell
$env:PYTHONDONTWRITEBYTECODE="1"
..\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
..\.venv\Scripts\python.exe -m streamlit run app.py --server.headless=true
```
