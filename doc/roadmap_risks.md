# Roadmap And Risks

## Current Limitations

The prototype is demo-ready but not production-ready.

Known limitations:

- Uses synthetic procurement data.
- Delay model is trained on a small sample table.
- No authentication or user roles.
- No production document parser for scanned PDFs.
- No persistent FAISS index file; retrieval is rebuilt from SQLite chunks for simplicity.
- No integration with ERP, Primavera, MS Project, Procore, SAP, or email.
- No human approval workflow for alert closure.
- No full evaluation dataset for RAG answer quality.

## Technical Risks

### RAG Accuracy

Risk:

- Retrieved chunks may not always contain enough context for complex questions.

Mitigation:

- Add better chunking by document section.
- Store metadata such as PO number, vendor, material, and dates.
- Add a RAG evaluation set with expected citations.

### Document Quality

Risk:

- Real procurement documents may be scanned, inconsistent, or poorly formatted.

Mitigation:

- Add OCR for scanned PDFs.
- Add templates for purchase orders and vendor contracts.
- Add validation for extracted dates and vendor names.

### ML Validity

Risk:

- Current delay prediction is trained on synthetic data.

Mitigation:

- Collect real historical delivery data.
- Validate predictions against actual delay outcomes.
- Calibrate risk scores by material category and project phase.

### Local Performance

Risk:

- Large models may be slow on laptop hardware.

Mitigation:

- Use `gemma3:4b` or `qwen2.5:7b`.
- Keep fallback extractive answers.
- Cache document retrieval.
- Use lightweight embeddings or local embedding models only when available.

### User Trust

Risk:

- Project managers may not trust AI outputs without evidence.

Mitigation:

- Always show citations.
- Show risk drivers.
- Let users inspect underlying PO/vendor data.
- Add confidence and explanation fields.

## Product Roadmap

### Next 1-2 Days

- Add visual polish to the Streamlit pages.
- Add downloadable alert report.
- Add filters by project phase, vendor, and material category.
- Add clearer risk-driver explanations for each prediction.
- Add sample email document.

### Next 1-2 Weeks

- Add OCR support.
- Add named entity extraction for PO number, vendor, material, delivery date, and ROJ date.
- Add persistent vector index metadata.
- Add RAG evaluation tests for all demo questions.
- Add CSV upload that updates the procurement dataset.

### Next 1-2 Months

- Integrate with real procurement systems.
- Add user accounts and project workspaces.
- Add alert assignment and resolution status.
- Add trend analysis across vendors and projects.
- Add schedule impact mapping to project activities.

## Future Architecture

Potential production architecture:

```text
Frontend
  -> Streamlit prototype or React dashboard

Backend API
  -> FastAPI
  -> Auth
  -> Project/workspace service

Data
  -> PostgreSQL for structured procurement data
  -> Object storage for documents
  -> Vector database for document chunks

AI
  -> Local or private-cloud LLM
  -> Embedding model
  -> RAG evaluation pipeline
  -> Delay prediction service

Integrations
  -> ERP
  -> Email
  -> Project schedule tools
  -> Vendor portals
```

## Final Hackathon Recommendation

For the hackathon, keep the story focused:

- Do not overclaim production readiness.
- Emphasize local-first construction procurement intelligence.
- Show citations and alerts clearly.
- Position the ML model as a prototype risk engine.
- Explain how real project data would replace synthetic data.
