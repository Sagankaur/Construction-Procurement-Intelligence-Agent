# Team Onboarding

## Project Goal

Build and present SiteSage AI as a construction procurement intelligence agent for the Kaya AI IIT India Hackathon 2026.

The app should show that an AI system can understand procurement context, forecast risk, and recommend action. The key message is: SiteSage helps project teams catch procurement delays before they affect site progress.

## What Each Folder Does

```text
code/app.py
```

Streamlit entry point. It loads the sidebar navigation and routes to each page.

```text
code/pages/
```

Streamlit pages:

- `01_Overview.py`: dashboard summary.
- `02_Upload_Documents.py`: upload and index procurement documents.
- `03_Ask_AI_Agent.py`: cited RAG Q&A.
- `04_Delay_Prediction.py`: delivery delay risk prediction.
- `05_Vendor_Risk.py`: vendor reliability scoring.
- `06_Alerts.py`: procurement alerts and actions.

```text
code/src/
```

Backend logic:

- `database.py`: SQLite tables and helpers.
- `document_loader.py`: text extraction, chunking, FAISS retrieval.
- `rag_engine.py`: prompt creation, Ollama call, cited fallback answer.
- `delay_model.py`: sample data loading and scikit-learn prediction.
- `vendor_risk.py`: vendor scoring.
- `alerts.py`: alert generation.

```text
code/data/
```

Synthetic procurement table used for demo analytics and ML.

```text
code/docs/
```

Sample procurement documents that can be indexed from the app.

```text
code/tests/
```

Backend tests for the important prototype behavior.

## Local Setup

From PowerShell:

```powershell
cd "C:\sagan ASUS\IIT\kaya\code"
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If the virtual environment is missing:

```powershell
cd "C:\sagan ASUS\IIT\kaya\code"
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run The App

```powershell
cd "C:\sagan ASUS\IIT\kaya\code"
..\.venv\Scripts\python.exe -B -m streamlit run app.py
```

Open:

```text
http://localhost:8501
```

## Run Tests

```powershell
cd "C:\sagan ASUS\IIT\kaya\code"
$env:PYTHONDONTWRITEBYTECODE="1"
..\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Expected result:

```text
Ran 3 tests
OK
```

## Optional Ollama Setup

The app works without Ollama because it has a cited fallback answer mode. For a local LLM demo:

```powershell
ollama pull qwen2.5:7b
$env:OLLAMA_MODEL="qwen2.5:7b"
$env:SITESAGE_USE_OLLAMA="1"
```

If Ollama is unavailable, the AI Agent page still answers from retrieved document chunks and cites sources.

## Team Roles For Demo Prep

- Presenter: owns the narrative, problem, solution, and demo flow.
- Backend owner: explains RAG, SQLite, FAISS, delay model, and tests.
- Frontend owner: explains Streamlit pages, dashboard flow, charts, and UX.
- Data owner: explains synthetic procurement data and how real data would replace it.
- Q&A owner: prepares answers about limitations, model accuracy, privacy, and next steps.

## Do Not Break Before Demo

- Do not remove `code/data/sample_procurement_data.csv`.
- Do not remove sample docs in `code/docs/`.
- Do not rename Streamlit page files unless updating `app.py`.
- Do not claim Ollama is required; it is optional.
- Do not claim the ML model is production-trained; it is a prototype trained on synthetic data.
