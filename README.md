# SiteSage AI

<p align="center">
  <img src="logo.jpeg" alt="SiteSage AI logo" width="88" />
  &nbsp;&nbsp;
  <img src="name.jpeg" alt="SiteSage AI wordmark" width="260" />
</p>

<p align="center">
  A local-first construction procurement intelligence prototype built for the Kaya AI IIT India Hackathon 2026.
</p>

SiteSage brings document search, delivery-risk prediction, vendor scoring, and operational alerts into one Streamlit application. It is designed as a demonstrable prototype: the repository includes synthetic procurement records and sample documents, and its core walkthrough works without an API key or hosted model.

## What it does

- Ingests PDF, TXT, Markdown, CSV, and Excel procurement documents.
- Chunks documents and retrieves relevant passages with a hashing vectorizer and FAISS.
- Produces source-linked extractive answers by default, with optional local Ollama generation.
- Estimates delivery delay risk from the included synthetic procurement history.
- Ranks vendors using delivery, quality, and communication signals.
- Converts delivery and vendor signals into prioritized procurement alerts.
- Relates delivery risk to phase float and critical-path heuristics.

## Try the included demo

### Local Python

Python 3.11 is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
SITESAGE_USE_OLLAMA=0 python -m streamlit run app.py
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` and set `$env:SITESAGE_USE_OLLAMA="0"` before running Streamlit. Open <http://localhost:8501>.

### Docker

The container intentionally uses the deterministic, no-LLM fallback. Ollama is not installed inside the image.

```bash
docker build -t sitesage-ai .
docker volume create sitesage-data
docker run --rm --name sitesage -p 8501:8501 \
  --mount type=volume,source=sitesage-data,target=/data \
  sitesage-ai
```

Open <http://localhost:8501>. The named volume preserves indexed documents and predictions between runs.

## Demo workflow

1. Review the **Overview** dashboard.
2. Open **Upload Documents** and index the bundled sample documents.
3. Ask: “Which deliveries are at risk this month?”
4. Score a structural-steel order in **Delay Prediction**.
5. Compare vendor signals in **Vendor Risk**.
6. Review the actions generated in **Alerts**.

Other useful questions include “Which vendors are high risk?” and “Which critical materials may affect the project schedule?”

## Architecture

```text
Browser
  |
  v
Streamlit multi-page UI
  |-- document upload ----------> text extraction -> chunking
  |                                      |             |
  |                                      v             v
  |                                  SQLite <---- FAISS retrieval
  |                                      |             |
  |                                      +---- cited answer
  |                                            (optional Ollama)
  |
  |-- procurement form --------> scikit-learn delay model
  |                                      |
  |                                      +--> schedule-impact heuristic
  |
  +-- sample procurement data -> vendor scoring -> prioritized alerts
```

| Area | Implementation |
| --- | --- |
| Interface | `app.py` and `pages/` |
| Document ingestion and retrieval | `src/document_loader.py` |
| Answer generation and citations | `src/rag_engine.py` |
| Delay prediction | `src/delay_model.py` |
| Vendor and schedule signals | `src/vendor_risk.py`, `src/schedule_impact.py` |
| Alerts | `src/alerts.py` |
| Persistence | `src/database.py` and SQLite |

## Optional local LLM

The retrieval and citation flow does not require Ollama. To add local generation, install Ollama on the host, pull a compatible model, and run the app outside the supplied container:

```bash
ollama pull qwen2.5:7b
export OLLAMA_MODEL=qwen2.5:7b
export SITESAGE_USE_OLLAMA=1
python -m streamlit run app.py
```

See [docs/ollama_setup.md](docs/ollama_setup.md) for Windows instructions and alternative models.

## Data and privacy

- Files are processed locally and stored in a local SQLite database.
- The default answer path does not send document text to an external API.
- The included CSV and documents are synthetic demo material.
- Delete the SQLite file (or Docker volume) to remove indexed demo state.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tests -v
SITESAGE_USE_OLLAMA=0 python -m streamlit run app.py --server.headless=true
```

The second command starts a server and is intended for a manual smoke test.

## Limitations

- This is a hackathon prototype, not a production procurement or scheduling system.
- The included model is trained on synthetic data; its score is a demonstration signal, not a calibrated operational forecast.
- Hashing-vector retrieval is lightweight and deterministic but less semantic than a learned embedding model.
- SQLite and the single-process UI are intended for local demos rather than multi-user deployment.
- Schedule impact is heuristic and does not replace a maintained CPM schedule.
- Ollama output quality and latency depend on the locally selected model and available hardware.
