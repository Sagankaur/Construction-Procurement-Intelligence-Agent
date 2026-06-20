# Technical Architecture

## System Overview

SiteSage AI is a local Streamlit application with a lightweight Python backend. It combines document retrieval, local LLM prompting, ML-based delay scoring, vendor scoring, and alert rules.

```text
User
  -> Streamlit pages
    -> SQLite document and prediction tables
    -> FAISS retrieval over document chunks
    -> Optional Ollama local LLM
    -> scikit-learn delay model
    -> vendor scoring and alerts
```

## Frontend

Framework: Streamlit

Entry point:

```text
app.py
```

Pages:

- Overview: high-level KPIs, risk chart, and top alerts.
- Upload Documents: sample document indexing and upload flow.
- Ask AI Agent: demo questions and cited RAG answers.
- Delay Prediction: form-based prediction and open order risk table.
- Vendor Risk: vendor score chart and reliability table.
- Alerts: critical, high, and medium procurement alerts.

## Data Storage

SQLite database:

```text
src/site_sage.db
```

This is generated locally and ignored by Git.

Main tables:

- `documents`: uploaded file name, extracted text, upload time.
- `document_chunks`: chunked text connected to each document.
- `predictions`: saved delay prediction outputs.

SQLite uses memory journal mode in the helper to avoid local Windows sandbox write issues.

## Document Processing And Retrieval

Source file:

```text
src/document_loader.py
```

Flow:

1. Extract text from uploaded PDF, TXT, CSV, Markdown, or Excel.
2. Normalize whitespace.
3. Split text into overlapping chunks.
4. Store document and chunks in SQLite.
5. Build hashed text vectors with `HashingVectorizer`.
6. Search chunks with FAISS inner product similarity.

Why hashed vectors:

- No external model download required.
- Deterministic and fast for hackathon demos.
- Works locally even without internet.

## RAG Answering

Source file:

```text
src/rag_engine.py
```

Flow:

1. Retrieve top document chunks from SQLite/FAISS.
2. Check whether the query has enough matching context.
3. If no support exists, return: "I do not have enough information..."
4. If Ollama is available and enabled, send the grounded prompt to Ollama.
5. If Ollama is unavailable, return an extractive answer with citations.

Citation format:

```text
[sample_purchase_order.txt#c0]
```

This means chunk `0` from `sample_purchase_order.txt`.

## Delay Prediction

Source file:

```text
src/delay_model.py
```

Model type:

- `RandomForestClassifier` for risk class.
- `RandomForestRegressor` for expected delay days.

Training data:

```text
data/sample_procurement_data.csv
```

Features:

- Material
- Category
- Vendor
- Quantity
- Contract value
- Priority
- Project phase
- Criticality
- Historical on-time rate
- Communication score
- Quality issues
- Lead time
- Days until promised delivery

Output:

- Risk score
- Risk level: Low, Medium, High
- Expected delay days
- Expected ROJ date
- Recommended action

## Vendor Risk

Source file:

```text
src/vendor_risk.py
```

Scoring signals:

- On-time rate
- Average delay days
- Open risky orders
- Communication score
- Quality issue count

Output:

- Vendor risk score
- Risk level
- Materials supplied
- Recommended vendor management action

## Alerts

Source file:

```text
src/alerts.py
```

Alert types:

- Delivery Risk
- Follow Up
- Vendor Risk
- Schedule Impact

Severity levels:

- Critical
- High
- Medium
- Low

Alerts are generated from delay risk, vendor risk, and critical delayed material rules.

## Verification Coverage

Tests are in:

```text
tests/test_backend.py
```

Covered:

- RAG answer includes expected text and citation.
- Unsupported question is declined.
- Delay prediction returns risk fields.
- Delivery risk table is populated.
- Vendor risk table is populated.
- Alerts are generated.

## Current Design Tradeoffs

- The prototype uses synthetic data, not real project data.
- The RAG fallback is extractive and deterministic, not a full reasoning LLM.
- The ML model is demo-ready but not production-validated.
- FAISS index is rebuilt from stored chunks during search, which is simple and robust for small demos.
- The app is local-first and avoids cloud dependencies.
