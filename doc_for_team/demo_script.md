# Demo Script

## Demo Goal

Show that SiteSage AI is a construction procurement copilot, not a generic chatbot. The demo should prove that it can learn project documents, answer with citations, predict delivery delay risk, rank vendors, and generate procurement alerts.

## Setup Before Demo

Run:

```powershell
cd "C:\sagan ASUS\IIT\kaya"
.\.venv\Scripts\python.exe -B -m streamlit run app.py
```

Open:

```text
http://localhost:8501
```

If using Ollama:

```powershell
ollama pull qwen2.5:7b
$env:OLLAMA_MODEL="qwen2.5:7b"
$env:SITESAGE_USE_OLLAMA="1"
```

If Ollama is not available, do not mention it as a blocker. The app has a deterministic cited fallback.

## 5-Minute Demo Flow

### 1. Open Overview

Say:

> SiteSage AI gives a project manager a procurement risk cockpit. It combines uploaded documents, structured procurement history, delay prediction, vendor scoring, and alerts.

Point out:

- Indexed document count.
- Open purchase orders.
- High-risk vendors.
- Critical alerts.
- Delivery risk chart.

### 2. Upload Documents

Go to `Upload Documents`.

Click:

```text
Load Sample Documents
```

Say:

> In a real project these would be POs, vendor contracts, delivery schedules, procurement reports, and emails. For the demo we load synthetic procurement documents.

Expected result:

- Sample documents are indexed.
- Table shows document names and chunk counts.

### 3. Ask AI Agent

Go to `Ask AI Agent`.

Ask:

```text
What is the expected ROJ date for steel?
```

Expected answer should include:

- `2026-06-24`
- A citation like `[sample_purchase_order.txt#c0]`

Say:

> The assistant answers only from indexed project documents and cites the exact retrieved chunk. If the answer is not in the documents, it says it does not have enough information.

Optional second question:

```text
Which vendors are high risk?
```

Expected vendors:

- ABC Metals
- ElectroPro Systems
- PowerCore Equipments

### 4. Delay Prediction

Go to `Delay Prediction`.

Use the default or choose:

- Material: Structural Steel
- Vendor: ABC Metals
- Priority: Critical
- Project Phase: Superstructure

Click:

```text
Predict Delay Risk
```

Say:

> The prediction combines vendor history, criticality, lead time, quality issues, communication score, and promised delivery date to estimate risk and expected ROJ date.

Point out:

- Risk level
- Risk score
- Expected delay days
- Expected ROJ date
- Recommendation

### 5. Vendor Risk

Go to `Vendor Risk`.

Say:

> SiteSage ranks vendors using on-time rate, average delay, open risky orders, communication score, and quality issues.

Point out high-risk vendors and recommended actions.

### 6. Alerts

Go to `Alerts`.

Say:

> The final output is not just an answer. It becomes an action list for the project manager: what to escalate, what to follow up, and what may affect the project schedule.

Point out:

- Critical schedule impact alerts.
- Delivery risk alerts.
- Vendor escalation alerts.
- Follow-up actions.

## Demo Questions

Use these exact questions:

```text
Which deliveries are at risk this month?
Which vendors are high risk?
What purchase orders need follow-up?
What materials are delayed?
What is the expected ROJ date for steel?
Which critical materials may affect the project schedule?
```

## Expected Story For Judges

Before SiteSage:

- Procurement teams manually chase updates.
- Risk is discovered late.
- Managers lack a single view of vendor and delivery risk.

After SiteSage:

- Documents become searchable with citations.
- Delivery risk is predicted before site impact.
- Vendor risk is ranked.
- Alerts turn risk into actions.

## Backup Plan If Something Fails

If Ollama is slow or unavailable:

- Continue with fallback cited answers.
- Say local LLM is optional and the prototype remains grounded in retrieved documents.

If document upload is not needed:

- Use `Load Sample Documents`.

If a browser page looks stale:

- Refresh the Streamlit tab.

If port 8501 is busy:

```powershell
..\.venv\Scripts\python.exe -B -m streamlit run app.py --server.port 8502
```
