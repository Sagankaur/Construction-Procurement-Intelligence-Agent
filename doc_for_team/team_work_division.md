# Team Work Division

## Team Context

SiteSage AI has three main workstreams:

- Streamlit app and dashboard integration.
- Procurement data, demo story, and validation.
- RAG, ML models, vendor scoring, and alert logic.

The team should divide work by ownership, but keep simple function contracts so the final app integrates cleanly.

## Member 1: Full Stack And App Owner

This member owns the working demo experience.

### Main Responsibilities

- Build and polish the Streamlit dashboard.
- Create upload flow for procurement documents.
- Connect all backend modules to the UI.
- Build pages or sections for:
  - AI procurement assistant.
  - Delay risk predictions.
  - Vendor risk scores.
  - Procurement alerts.
- Display charts, tables, metrics, and source citations cleanly.
- Handle SQLite integration from the app side.
- Make sure the final demo flow feels like a construction procurement copilot, not a generic chatbot.

### Primary Files

```text
app.py
pages/
src/database.py
README.md
```

### Demo Ownership

This member should run the live app during the final presentation and make sure each page works smoothly.

## Member 2: Data, Domain, QA, And Demo Content Owner

This member can use an electronics background well by focusing on structured data, operational logic, validation, and the demo story. If they know Python or Pandas, they can also help clean and extend the dataset.

### Main Responsibilities

- Prepare realistic synthetic procurement data.
- Create sample purchase orders, vendor contracts, and delivery scenarios.
- Define construction procurement cases such as:
  - Delayed steel delivery.
  - Cement shortage.
  - Vendor reliability issue.
  - Transport bottleneck.
  - Critical material affecting the project schedule.
- Maintain demo questions and expected answers.
- Test the app like a project manager would.
- Check whether AI answers are grounded in uploaded documents.
- Help prepare the pitch, problem statement, and hackathon explanation.

### Primary Files

```text
data/sample_procurement_data.csv
docs/sample_purchase_order.txt
docs/sample_vendor_contract.txt
doc_for_team/demo_script.md
doc_for_team/hackathon_pitch.md
```

### Demo Ownership

This member should explain the construction procurement problem, why delays matter, and how the sample data represents real site workflows.

## Member 3: ML, RAG, And Intelligence Owner

This member owns the AI and analytics behavior.

### Main Responsibilities

- Build the RAG pipeline:
  - Load documents.
  - Chunk text.
  - Create embeddings.
  - Retrieve relevant chunks.
  - Generate answers using Ollama when available.
  - Return citations for retrieved chunks.
- Make sure unsupported questions return a clear not-enough-information answer.
- Build or tune the delay prediction model.
- Build vendor reliability scoring.
- Generate procurement alerts from data, risk scores, and delay predictions.
- Keep model logic simple enough for a reliable hackathon demo.

### Primary Files

```text
src/document_loader.py
src/rag_engine.py
src/delay_model.py
src/vendor_risk.py
src/alerts.py
models/
```

### Demo Ownership

This member should explain how RAG, delay prediction, vendor scoring, and alert generation work.

## Integration Contracts

Each member should build around simple function contracts. This avoids integration problems near the deadline.

```python
answer_question(question: str) -> dict
```

Expected output:

```python
{
    "answer": "Procurement-grounded answer",
    "sources": ["document name or chunk citation"]
}
```

```python
predict_delay_risk(procurement_df) -> dataframe
```

Expected output should include delivery or purchase order rows with risk labels or probabilities.

```python
score_vendor_risk(procurement_df) -> dataframe
```

Expected output should include vendors with reliability scores and risk categories.

```python
generate_alerts(procurement_df, delay_df, vendor_df) -> list
```

Expected output should be a list of actionable procurement alerts.

## Suggested Hackathon Timeline

### Day 1

- Member 1 builds the Streamlit page structure and placeholder UI.
- Member 2 prepares sample procurement data and documents.
- Member 3 builds basic RAG, delay prediction, vendor scoring, and alert stubs.

### Day 2

- Member 1 connects backend outputs into the dashboard.
- Member 2 tests demo questions and improves sample scenarios.
- Member 3 improves retrieval quality, risk scores, and alert explanations.

### Final Preparation

- Run the app end to end.
- Upload sample documents.
- Ask the demo questions.
- Show delay predictions, vendor risks, and alerts.
- Confirm every answer either cites retrieved document chunks or says there is not enough information.

## Demo Question Ownership

- Member 1 verifies that each question works in the UI.
- Member 2 verifies that the expected answer makes procurement sense.
- Member 3 verifies that the answer is grounded in RAG or model outputs.

Use these demo questions:

- Which deliveries are at risk this month?
- Which vendors are high risk?
- What purchase orders need follow-up?
- What materials are delayed?
- What is the expected ROJ date for steel?
- Which critical materials may affect the project schedule?

## Team Coordination Rules

- Keep each change small and commit with a clear message.
- Do not mix UI, data, and ML changes in one commit unless required for integration.
- Before merging, run the app or tests relevant to the changed area.
- Use shared demo data names and column names consistently.
- If a backend function changes its output format, tell the app owner immediately.
- Keep the final demo branch stable during the last few hours.
