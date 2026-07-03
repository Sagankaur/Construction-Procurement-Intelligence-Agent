# SiteSage AI — Stage 1 Submission Pack

**Project:** SiteSage AI — Construction Procurement Intelligence Agent  
**Hackathon:** Kaya AI IIT India Hackathon 2026  
**Track:** Track 2 — Supply Chain (procurement intelligence focus)  
**Status:** Working local prototype with synthetic baseline data  
**Repository:** `[Add GitHub URL before submission]`

---

## 1. Project Story

Large construction projects live or die on procurement — yet the people responsible for schedule lookahead still chase answers across spreadsheets, purchase orders, vendor contracts, emails, and site calls. We built **SiteSage AI** because we kept seeing the same pattern: a critical delivery slips quietly, and the site only reacts after float is gone.

**SiteSage AI** is a local procurement command center for project managers. It connects three layers that are usually separate:

1. **Document intelligence** — ask questions about POs and contracts with cited answers.  
2. **Predictive risk** — machine-learning scores on open deliveries and vendors.  
3. **Action workflow** — schedule impact flags and procurement alerts a manager can act on today.

We aligned the prototype around a processed procurement dataset (`procurement_master.csv`, 517 rows), sample documents grounded in that data, and a six-page Streamlit dashboard that runs on a laptop without cloud dependency.

**What we learned:** Construction teams do not need another generic chatbot. They need **evidence** (citations), **forecasts** (delay and ROJ), and **prioritized actions** (alerts) in one workflow. We also learned to be precise about scheduling language — promised delivery, expected ROJ, and schedule impact mean different things on a real site.

**How we built it:** Python backend modules for RAG, delay prediction, vendor scoring, schedule impact mapping, and alerts; Streamlit UI pages; SQLite document storage; FAISS retrieval; optional Ollama for local LLM inference; scikit-learn RandomForest models trained via `scripts/process.py`.

---

## 2. Problem Statement

Construction supply chains generate enormous data — POs, vendor commitments, inspection status, dispatch updates — but **no single view** tells a project manager:

- Which open deliveries are at risk this month  
- Which vendors are unreliable  
- Which purchase orders need follow-up now  
- Whether a delay will consume schedule float or block the critical path  

Procurement status is fragmented. Delay risk is tracked manually. Critical material issues surface **after** downstream activities are already impacted.

On the **Kaya IIT Construction Tower** demo scenario, a slipped structural cement pour (PO-2133) can delay structural steel ROJ, Foundation work, and Superstructure sequencing — but only if someone connects the documents, the data, and the schedule early enough.

---

## 3. Inspiration

**Kaya AI** builds Amber to learn project context and help construction teams decide before damage is done. The Kaya hackathon Supply Chain and Procurement tracks ask a direct question: *What would it look like if construction supply chains finally had a brain?*

We were inspired by:

- **Real site pain** — PMs and procurement coordinators losing hours reconciling PO status across tools.  
- **Kaya's Amber pattern** — context → prediction → action, not chat for its own sake.  
- **Local-first AI** — sensitive project data should stay on the demo machine; Ollama is optional, not required.  
- **Honest prototyping** — show baseline ML metrics and cited RAG answers judges can verify live, without overclaiming production readiness.

---

## 4. Solution Overview

SiteSage AI is a **local-first procurement copilot** that unifies:

| Layer | Capability |
| --- | --- |
| **Knowledge** | Upload procurement documents; retrieve cited answers via RAG |
| **Prediction** | Score delay risk (Low / Medium / High), forecast expected delay days and expected ROJ date |
| **Operations** | Rank vendor reliability, map schedule impact, generate prioritized alerts |

**End-to-end flow:**

```text
Upload POs & contracts → Index in SQLite + FAISS
       ↓
Ask AI Agent (cited RAG answers)
       ↓
Delay Prediction + Vendor Risk (ML + rules on procurement_master.csv)
       ↓
Schedule Impact Mapping + Procurement Alerts
       ↓
Project manager actions (escalate, follow up, mitigate)
```

**Demo anchor:** PO-2133 (Cement, Structural — Badlands Components LLC) links document Q&A, delay prediction, vendor escalation, and schedule risk in one narrative.

---

## 5. Key Features

### Dashboard & document intelligence
- Six-page Streamlit app: Overview, Upload Documents, Ask AI Agent, Delay Prediction, Vendor Risk, Alerts  
- Upload PDF, TXT, CSV, Markdown, Excel procurement files  
- Load sample documents aligned to processed dataset  
- Regex extraction of PO numbers, dates, materials, and vendors into SQLite  

### Retrieval-Augmented Generation (RAG)
- FAISS + HashingVectorizer retrieval over document chunks  
- Optional Ollama local LLM (`qwen2.5:7b` recommended)  
- Deterministic cited fallback when Ollama is unavailable  
- Declines unsupported questions when context is insufficient  

### Delay risk prediction
- RandomForest **classifier** (Low / Medium / High risk)  
- RandomForest **regressor** (expected delay days)  
- Expected ROJ date = promised delivery + expected delay  
- Batch scoring of all open purchase orders  
- Interactive prediction form with risk score, recommendation, and timeline  

### Vendor risk analysis
- Vendor reliability table: on-time rate, average delay, open risky orders, communication score, quality issues  
- High-risk vendor highlighting (e.g., Badlands Components LLC, Granite Valley Mfg)  
- Vendor 360° detail and comparison views  

### Schedule impact mapping
- Phase-level float heuristic: **On Track** / **Float Consumed** / **Critical Path Blocked**  
- Overview chart summarizing impacted materials by phase  

### Procurement alerts
- **Delivery Risk** — high delay-risk open orders  
- **Follow Up** — POs due within 7 days  
- **Vendor Risk** — high-risk supplier escalation  
- **Schedule Impact** — critical materials at risk or delayed  

---

## 6. Built With

| Category | Technologies |
| --- | --- |
| **Language** | Python 3 |
| **Frontend** | Streamlit |
| **Data & ML** | Pandas, NumPy, scikit-learn, joblib |
| **Retrieval** | FAISS CPU, scikit-learn HashingVectorizer |
| **Storage** | SQLite |
| **Visualization** | Plotly |
| **Documents** | pypdf, openpyxl |
| **Optional LLM** | Ollama (`qwen2.5:7b`, `gemma3:4b`, or `llama3.1:8b`) |
| **Testing** | Python `unittest` |

**Deployment model:** Local laptop demo (Windows/macOS). No cloud API required for core functionality.

**Try it out (fill before portal submission):**

| Link | Purpose |
| --- | --- |
| `[GitHub repository URL]` | Source code |
| `[Unlisted YouTube / Loom URL]` | 2-minute walkthrough video |
| `http://localhost:8501` | Local demo (run `streamlit run app.py`) |

---

## 7. System Architecture Summary

```text
Streamlit UI (app.py + pages/)
        │
        ├── SQLite (site_sage.db)
        │     documents · document_chunks · procurement_facts · predictions
        │
        ├── RAG pipeline
        │     document_loader.py → chunk · embed · FAISS search
        │     rag_engine.py      → Ollama or extractive cited answers
        │
        ├── ML & analytics
        │     delay_model.py     → classifier + regressor · delivery risk table
        │     vendor_risk.py     → vendor scoring · 360° views
        │     schedule_impact.py → float / critical-path mapping
        │     alerts.py          → prioritized procurement alerts
        │
        └── Data
              data/processed/procurement_master.csv  (primary, 517 rows)
              data/processed/vendor_master.csv
              docs/sample_purchase_order.txt
              docs/sample_vendor_contract.txt
              models/*.joblib  (optional trained artifacts)
```

**Design principles:** local-first, cited evidence, modular backend contracts, synthetic baseline data swappable for real project history.

Full detail: `doc_for_team/technical_architecture.md`  
Scheduling terms: `doc_for_team/procurement_scheduling_glossary.md`

---

## 8. Machine Learning Summary

### Models
| Component | Algorithm | Purpose |
| --- | --- | --- |
| Delay risk classifier | RandomForestClassifier | Predict Low / Medium / High delay risk |
| Delay duration regressor | RandomForestRegressor | Forecast expected delay days beyond promised delivery |

### Training pipeline
- Script: `scripts/process.py`  
- Primary dataset: `data/processed/procurement_master.csv` (517 procurement rows)  
- Features: material, category, vendor, quantity, contract value, priority, project phase, criticality, historical on-time rate, communication score, lead time, days until promised delivery  
- Evaluation: **20% held-out test split** (stratified for classification; minority-class oversampling on training set)  
- Artifacts: `models/delay_risk_classifier.joblib`, `models/delay_risk_regressor.joblib`, `models/feature_encoders.joblib`

### Baseline metrics (synthetic holdout — not production claims)

| Metric | Result |
| --- | --- |
| Delay risk classification accuracy | **~75%** on held-out test set |
| Expected delay regression MAE | **~1.20 days** on held-out test set |

**Important:** These are **prototype baseline results on synthetic procurement data**. Production deployment would require real project delivery history, retraining, calibration, and ongoing monitoring. The app also applies business-rule adjustments (urgency, vendor, quality, criticality) when computing final risk scores and recommendations.

### Runtime inference
- `delay_model.py` loads joblib artifacts when present; otherwise trains fallback pipelines on loaded procurement data  
- `get_delivery_risk_table()` batch-scores all open orders for dashboard and alerts  

---

## 9. RAG Overview

### Pipeline
1. **Ingest** — extract text from uploaded files; chunk (700 chars, 120 overlap); store in SQLite  
2. **Retrieve** — HashingVectorizer embeddings + FAISS inner-product search (top-k chunks)  
3. **Ground** — relevance gate: minimum score + query-term overlap; decline if unsupported  
4. **Answer** — Ollama grounded prompt when enabled; otherwise extractive fallback with sentence-level citations  
5. **Cite** — format `[filename#cN]` (e.g., `[sample_purchase_order.txt#c1]`)

### Demo behavior (verified against sample documents)
| Question | Grounded answer includes |
| --- | --- |
| What is the expected ROJ date for steel? | **2026-07-11** (PO-2133) |
| Which vendors are high risk? | Badlands Components LLC, Granite Valley Mfg, Zenith Alloy Solutions, Ironclad Assemblies |
| What purchase orders need follow-up? | PO-2133, PO-2179, PO-2125, PO-2008 |
| Which critical materials may affect the project schedule? | PO-2133, PO-2006, PO-2017, PO-2473 |

Full Q&A table: `doc_for_team/demo_script.md`

---

## 10. Vendor Risk Analysis

### Signals
- Historical on-time delivery rate  
- Average delay days across orders  
- Count of open risky orders  
- Communication score  
- Quality issue count  

### Outputs
- Vendor risk score (0–100) and risk level (Low / Medium / High)  
- Materials supplied and order counts  
- Recommended vendor management action  
- Vendor 360° profile: spend, categories, status breakdown, monthly trend  

### Demo vendors to highlight
| Vendor | Why it matters |
| --- | --- |
| **Badlands Components LLC** | Highest-priority escalation; PO-2133, PO-2008, PO-2473 |
| **Granite Valley Mfg** | 15 high-risk open orders in vendor notes |
| **Zenith Alloy Solutions** | 14 high-risk open orders |
| **Ironclad Assemblies** | Repeated delay forecasts on structural / mechanical materials |

Source: `docs/sample_vendor_contract.txt` + `vendor_master.csv` / procurement aggregates

---

## 11. Schedule Impact Mapping

### What it does
Maps procurement delays to **phase-level schedule float** to indicate whether a slip is absorbable or critical-path threatening.

### Logic (`src/schedule_impact.py`)
| Phase | Float budget (days) |
| --- | --- |
| Foundation | 5 |
| Superstructure | 3 |
| MEP Fitouts | 2 |
| Finishes | 7 |
| Default (unlisted phase) | 4 |

| Status | Condition |
| --- | --- |
| On Track | delay ≤ 0 |
| Float Consumed | 0 < delay ≤ phase float |
| Critical Path Blocked | delay > phase float |

**Delay input:** `actual_delay_days` from dataset, or `observed_delay_days` for open orders — distinct from ML `expected_delay_days` (documented in glossary).

### Prototype scope
This is a **heuristic demo mapping**, not Primavera / MS Project integration. Future work: compare forecast ROJ against schedule-required on-site dates from lookahead tools.

---

## 12. Procurement Alerts

Generated in `src/alerts.py` from delivery risk, vendor risk, and raw procurement status.

| Alert type | Trigger (summary) | Severity |
| --- | --- | --- |
| **Delivery Risk** | Open order risk score ≥ 68 | High / Critical |
| **Follow Up** | Promised delivery within 7 days | Medium |
| **Vendor Risk** | Vendor risk level = High | High |
| **Schedule Impact** | Critical material + At Risk / Delayed status | Critical |

Each alert includes title, detail, recommended action, and due date where applicable.

**Demo examples:** PO-2133 delivery risk; Badlands vendor escalation; critical Foundation / Superstructure materials.

---

## 13. Challenges Faced

| Challenge | How we addressed it |
| --- | --- |
| **Fragmented demo data** | Migrated to `procurement_master.csv` and aligned RAG sample documents, demo script, and pitch to the same PO numbers and vendors |
| **RAG without cloud APIs** | HashingVectorizer + FAISS for local retrieval; extractive fallback when Ollama is slow or unavailable |
| **Scheduling terminology confusion** | Documented promised delivery vs expected ROJ vs schedule impact in `procurement_scheduling_glossary.md` |
| **ML / document alignment** | Seeded documents reference PO-2133, Badlands Components LLC, and ROJ 2026-07-11 so RAG and ML tell one story |
| **Performance on dashboard load** | Batch vectorized inference for open-order risk table (replaced per-row prediction loop) |
| **Vendor master / procurement vendor mismatch** | Prototype uses procurement-derived vendor aggregates; documented as known data-pipeline limitation |
| **Synthetic baseline credibility** | Report ~75% / ~1.20-day MAE as holdout baselines with explicit non-production disclaimer |

---

## 14. Future Improvements

### Near term (post–Stage 1)
- OCR for scanned PDF purchase orders  
- Persistent FAISS index and chunk metadata (PO, vendor, material tags)  
- RAG evaluation test suite for all six demo questions  
- CSV upload to refresh procurement data live  
- Draft follow-up email action (Ollama-generated vendor escalation)  

### Medium term
- Integrate **schedule-required ROJ** from Primavera / MS Project lookahead  
- Compare forecast ROJ vs required on-site date per activity  
- Real project history for model retraining and calibration  
- ERP / Procore / email integration  
- User accounts, project workspaces, alert assignment and closure workflow  

### Production hardening
- Authentication and role-based access  
- Model monitoring and drift detection  
- Expanded RAG evaluation and human-in-the-loop feedback  
- Security review for document storage and local LLM deployment  

Detail: `doc_for_team/roadmap_risks.md`

---

## 15. Team Contributions (High Level)

> **Before submission:** Replace role placeholders with each member's **name** and **IIT affiliation** (2–4 members per hackathon rules).

| Member | Role | Primary contributions |
| --- | --- | --- |
| **[Name 1]** · *[IIT affiliation]* | Full stack & app owner | Streamlit dashboard, page integration, SQLite UI flow, demo presentation, `app.py` / `pages/` |
| **[Name 2]** · *[IIT affiliation]* | Data, domain & QA | `procurement_master.csv`, sample documents, demo script, submission narrative, procurement scenario validation |
| **[Name 3]** · *[IIT affiliation]* | ML, RAG & intelligence | RAG pipeline, delay model, vendor scoring, alerts, schedule impact, `scripts/process.py`, backend tests |

**Collaboration model:** Small commits, shared function contracts (`get_answer`, `predict_delay_risk`, `get_vendor_risk_table`, `generate_alerts`), end-to-end demo rehearsal before submission.

Detail: `doc_for_team/team_work_division.md`

---

## 16. 2-Minute Walkthrough Video Outline

**Target length:** 120 seconds · **Format:** Unlisted YouTube or Loom · **Tone:** Clear, confident, evidence-focused

| Time | Visual | Narration |
| --- | --- | --- |
| **0:00–0:15** | Problem slide or site photo | "Procurement delays hide in spreadsheets and emails — SiteSage AI gives project managers one local command center." |
| **0:15–0:30** | Overview dashboard | "Open POs, high-risk deliveries, vendor escalations, and schedule impact — one cockpit." |
| **0:30–0:50** | Upload Documents → Load Sample Documents | "We index procurement documents aligned to our dataset — PO register and vendor risk notes." |
| **0:50–1:10** | Ask AI Agent: *"What is the expected ROJ date for steel?"* | "RAG answers with **citations** — here, structural steel ROJ **July 11** tied to **PO-2133**." |
| **1:10–1:25** | Delay Prediction — PO-2133 parameters → Generate Prediction Profile | "ML scores delay risk — about **75%** classification baseline and **1.2-day** regression MAE on our synthetic holdout." |
| **1:25–1:40** | Vendor Risk + Alerts pages | "Badlands Components LLC escalates; alerts tell the PM what to follow up before the site stops." |
| **1:40–2:00** | Architecture diagram or closing slide | "SiteSage connects cited documents, predictive risk, and action — local-first, Kaya-aligned, ready for real project data." |

**Recording checklist:**
- [ ] Show citation chunk label on screen  
- [ ] Speak ML metrics once with "synthetic baseline" qualifier  
- [ ] Name PO-2133 and Badlands Components LLC  
- [ ] End with Kaya / supply chain one-liner  

---

## 17. Demo Checklist for Judges

Use this during live demo or video recording. Full script: `doc_for_team/demo_script.md`

### Setup
- [ ] `pip install -r requirements.txt` completed  
- [ ] `streamlit run app.py` → `http://localhost:8501`  
- [ ] Optional: Ollama running with `qwen2.5:7b` (not required)  
- [ ] `data/processed/procurement_master.csv` present  

### 1. Overview (30 sec)
- [ ] Open purchase order count visible  
- [ ] High-risk delivery count visible  
- [ ] Schedule impact chart (On Track / Float Consumed / Critical Path Blocked)  
- [ ] Critical alerts listed  

### 2. Upload Documents (20 sec)
- [ ] Click **Load Sample Documents**  
- [ ] `sample_purchase_order.txt` and `sample_vendor_contract.txt` indexed with chunk counts  

### 3. Ask AI Agent (40 sec)
- [ ] Ask: *"What is the expected ROJ date for steel?"*  
- [ ] Answer includes **2026-07-11** and **PO-2133**  
- [ ] Citation visible (e.g., `[sample_purchase_order.txt#c1]`)  
- [ ] Optional: *"Which vendors are high risk?"* → Badlands, Granite Valley Mfg, Zenith, Ironclad  

### 4. Delay Prediction (30 sec)
- [ ] Material: **Cement** · Vendor: **Badlands Components LLC**  
- [ ] Order: **2026-06-10** · Promised: **2026-07-02** · Phase: **Foundation** · Qty: **67**  
- [ ] Click **Generate Prediction Profile**  
- [ ] Risk level, risk score, expected delay days, expected ROJ near **2026-07-11**  

### 5. Vendor Risk (20 sec)
- [ ] Badlands Components LLC visible with high risk  
- [ ] Granite Valley Mfg / Zenith Alloy Solutions in top ranks  
- [ ] Recommendation text shown  

### 6. Alerts (20 sec)
- [ ] Delivery Risk alert for high-risk PO  
- [ ] Follow-up alert for due-soon PO (e.g., PO-2133, PO-2179)  
- [ ] Vendor Risk or Schedule Impact alert visible  

### Judge talking points (if asked)
- [ ] "Not just a chatbot" — ML + vendor risk + schedule mapping + alerts  
- [ ] "Local-first" — no cloud required; Ollama optional  
- [ ] "Metrics are synthetic baseline" — ~75% accuracy, ~1.20-day MAE on holdout  
- [ ] "Aligned with Kaya Amber" — context → prediction → action  

---

## Appendix: Stage 1 Deliverables Mapping

| Hackathon requirement | Where covered |
| --- | --- |
| Written project proposal | This document (Sections 1–14) |
| Project Story (portal markdown) | Section 1 + Section 3 |
| Built With (portal) | Section 6 |
| Problem & solution | Sections 2, 4 |
| 2-minute video | Section 16 (outline) + `[video URL]` in Section 6 |
| Slide deck (max 10 slides) | Use slide bullets in `hackathon_pitch.md` |
| Team names & IIT affiliations | Section 15 (fill before submit) |
| Try it out links | Section 6 |
| Live demo readiness | Section 17 |

**Related team docs:** `hackathon_pitch.md` · `demo_script.md` · `technical_architecture.md` · `procurement_scheduling_glossary.md`

---

*Last updated for Stage 1 submission — Kaya AI IIT India Hackathon 2026*
