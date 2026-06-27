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

> In a real project these would be POs, vendor contracts, delivery schedules, procurement reports, and emails. For the demo we load procurement documents aligned to our processed dataset.

Expected result:

- `sample_purchase_order.txt` and `sample_vendor_contract.txt` are indexed.
- Table shows document names and chunk counts.

### 3. Ask AI Agent

Go to `Ask AI Agent`.

Ask:

```text
What is the expected ROJ date for steel?
```

Expected answer should include:

- `2026-07-11` (linked structural steel ROJ, dependent on PO-2133)
- Reference to PO-2133 or structural cement from Badlands Components LLC
- A citation like `[sample_purchase_order.txt#c1]`

Say:

> The assistant answers only from indexed project documents and cites the exact retrieved chunk. If the answer is not in the documents, it says it does not have enough information.

Optional second question:

```text
Which vendors are high risk?
```

Expected vendors (from `sample_vendor_contract.txt`):

- Badlands Components LLC
- Granite Valley Mfg
- Zenith Alloy Solutions
- Ironclad Assemblies

### 4. Delay Prediction

Go to `Delay Prediction`.

Say:

> Now we score the same critical delivery the documents flagged — PO-2133 structural cement on the Foundation package.

Select these values (from `procurement_master.csv` / PO-2133):

- Material: Cement
- Vendor: Badlands Components LLC
- Quantity: 67
- Purchase Order Date: 2026-06-10
- Promised Delivery Date: 2026-07-02
- Priority: Critical
- Project Phase: Foundation

Click:

```text
Generate Prediction Profile
```

Say:

> The prediction combines vendor history, criticality, lead time, quality issues, communication score, and promised delivery date to estimate risk and expected ROJ date.

Point out:

- Risk level (expect High or Medium)
- Risk score
- Expected delay days
- Expected ROJ date (should be near `2026-07-11`, matching the document register)
- Recommendation

**Presenter shortcut:** The form also loads with app defaults (Cement, Canyon Fabricators LLC, Critical priority). Either path works; PO-2133 is preferred because it matches the RAG story.

### 5. Vendor Risk

Go to `Vendor Risk`.

Say:

> SiteSage ranks vendors using on-time rate, average delay, open risky orders, communication score, and quality issues.

Point out high-risk vendors and recommended actions. Names to highlight:

- Badlands Components LLC (escalation target; PO-2133, PO-2008, PO-2473)
- Granite Valley Mfg (15 high-risk open orders)
- Zenith Alloy Solutions
- Ironclad Assemblies

### 6. Alerts

Go to `Alerts`.

Say:

> The final output is not just an answer. It becomes an action list for the project manager: what to escalate, what to follow up, and what may affect the project schedule.

Point out:

- Critical schedule impact alerts (Foundation / Superstructure materials).
- Delivery risk alerts for PO-2133, PO-2179, PO-2006.
- Vendor escalation alerts for Badlands Components LLC and other high-risk vendors.
- Follow-up actions for POs due before 2026-07-04.

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

## Expected RAG Answers (Grounded in Sample Documents)

All answers below must come from indexed `docs/sample_purchase_order.txt` and `docs/sample_vendor_contract.txt`. If Ollama is off, the fallback extractive answer should still include these facts.

| Question | Expected grounded content | Source document |
| --- | --- | --- |
| Which deliveries are at risk this month? | High-risk deliveries this month: **10**; multiple orders with **Risk level: High** and **Status: At Risk** | `sample_purchase_order.txt` |
| Which vendors are high risk? | **Badlands Components LLC**, **Granite Valley Mfg**, **Zenith Alloy Solutions**, **Ironclad Assemblies** (and other vendors under HIGH-RISK VENDORS) | `sample_vendor_contract.txt` |
| What purchase orders need follow-up? | **PO-2133**, **PO-2179**, **PO-2125**, **PO-2008** (follow-up before 2026-07-04) | `sample_purchase_order.txt` |
| What materials are delayed? | **Cement (Structural)** on PO-2133, **Cement (Thermal Management)** on PO-2179, **Formwork (Mechanical)** on PO-2006, **Formwork (Optical)** on PO-2017 | `sample_purchase_order.txt` |
| What is the expected ROJ date for steel? | **2026-07-11** (structural steel ROJ linked to PO-2133) | `sample_purchase_order.txt` |
| Which critical materials may affect the project schedule? | **PO-2133**, **PO-2006**, **PO-2017**, **PO-2473** | `sample_purchase_order.txt` |

## Key Reference Data (Processed Dataset)

Register date in sample documents: **2026-06-27**

| PO | Material | Vendor | Promised delivery | Expected ROJ | Risk |
| --- | --- | --- | --- | --- | --- |
| PO-2133 | Cement (Structural) | Badlands Components LLC | 2026-07-02 | 2026-07-11 | High |
| PO-2179 | Cement (Thermal Management) | Eagle Ridge Components | 2026-07-02 | 2026-07-13 | High |
| PO-2125 | Formwork (Mechanical) | Lowland Metal Works | 2026-07-02 | 2026-07-10 | High |
| PO-2008 | Cement (Electrical) | Badlands Components LLC | 2026-07-03 | 2026-07-10 | High |
| PO-2006 | Formwork (Mechanical) | Cascade Tooling Solutions | 2026-07-13 | 2026-07-22 | High |
| PO-2017 | Formwork (Optical) | Vega Electronics Ltd | 2026-07-09 | 2026-07-17 | High |
| PO-2473 | Formwork (Optical) | Badlands Components LLC | 2026-07-06 | 2026-07-16 | High |

Materials in the processed dataset: **Cement**, **Formwork** (with category specifications such as Structural, Electrical, Mechanical, Optical).

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
