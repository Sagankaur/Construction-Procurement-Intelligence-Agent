# Hackathon Pitch

## Pitch Title

**SiteSage AI: Construction Procurement Intelligence Agent**

*Track 2 — Supply Chain / Procurement intelligence for the Kaya AI IIT India Hackathon 2026*

---

## Elevator Pitch (30 seconds)

> Construction schedules slip when procurement problems surface too late. **SiteSage AI** is a local procurement copilot that turns POs and vendor contracts into cited answers, delay risk scores, vendor rankings, schedule impact flags, and manager-ready alerts — before materials miss site.

---

## Problem

On every major project, teams chase the same questions:

- What is approved and what is still open?
- Which vendors are slipping?
- Which POs need follow-up this week?
- Will critical materials arrive when the site needs them?

The answers live in **spreadsheets, contracts, emails, and phone calls** — not in one place. By the time a steel package, formwork batch, or MEP delivery is flagged, **float is gone and the critical path is already under pressure**.

---

## Solution

SiteSage AI is a **local-first procurement command center** that connects documents, data, and action:

| Capability | What it does |
| --- | --- |
| **RAG document Q&A** | Upload POs and contracts; ask natural-language questions; get **cited answers** from indexed chunks (Ollama optional, extractive fallback built in). |
| **Delay risk ML** | RandomForest **classifier + regressor** score Low/Medium/High risk and forecast **expected delay days** and **expected ROJ date**. |
| **Vendor risk analysis** | Rank suppliers by on-time rate, open risky orders, communication, and quality signals. |
| **Schedule impact mapping** | Map delays to per-phase **float consumption** and **critical-path blocked** status. |
| **Procurement alerts** | Turn risk into **Delivery Risk**, **Follow-Up**, **Vendor Risk**, and **Schedule Impact** actions. |

One dashboard. No cloud dependency required for the demo.

---

## Technical Proof (Accurate Baseline Metrics)

Models are trained via `scripts/process.py` on **`procurement_master.csv`** (517 synthetic procurement rows derived from supply-chain reference data). Evaluation uses a **20% held-out test split** with the same feature pipeline the app loads at runtime.

| Model | Metric | Baseline result |
| --- | --- | --- |
| **Delay risk classifier** (RandomForest) | Test-set accuracy | **~75%** |
| **Delay duration regressor** (RandomForest) | Mean absolute error (MAE) | **~1.20 days** |

**How to say this to judges:** *"On our synthetic baseline dataset, the classifier reaches about 75% accuracy on held-out delay-risk classes, and the regressor forecasts delay duration within roughly 1.2 days on average. This is a prototype baseline — production would require real project history and ongoing calibration."*

**What we do not claim:** production-grade accuracy, real-project validation, or CPM-grade schedule integration (see `procurement_scheduling_glossary.md`).

---

## Why It Is Different

Most hackathon teams stop at a document chatbot. SiteSage closes the loop:

1. **Grounded knowledge** — RAG with chunk citations; declines when context is missing.
2. **Predictive layer** — tabular ML on procurement features, not just text retrieval.
3. **Operational layer** — vendor scores, schedule impact mapping, and prioritized alerts.

Construction-specific entities throughout: **PO number, vendor, material, promised delivery, ROJ, project phase, criticality**.

Runs **locally** on a laptop — important for sensitive project data.

---

## Kaya AI Alignment

Kaya's Amber concept learns **project context** and helps teams **decide before damage is done**. SiteSage applies that pattern to procurement:

- Learns from uploaded **project documents** (RAG).
- Predicts **delivery and vendor risk** from structured history (ML).
- Surfaces **schedule impact** and **follow-up actions** (alerts).

This is supply-chain intelligence that connects *what we know* → *what will go wrong* → *what to do now*.

---

## Target Persona

**Primary:** Project manager coordinating procurement and schedule lookahead.

**Secondary:** Procurement manager, planning engineer, site coordinator, commercial / vendor management.

---

## Demo Proof Points

Run these in order (full script: `demo_script.md`):

1. **Overview** — open PO count, high-risk deliveries, critical alerts, schedule impact chart.
2. **Upload Documents** — load `sample_purchase_order.txt` and `sample_vendor_contract.txt`.
3. **Ask AI Agent** — *"What is the expected ROJ date for steel?"* → **2026-07-11**, citation from PO register (PO-2133).
4. **Delay Prediction** — score **Cement / Badlands Components LLC / PO-2133** parameters; show risk score, expected delay, expected ROJ.
5. **Vendor Risk** — highlight **Badlands Components LLC**, **Granite Valley Mfg**, **Zenith Alloy Solutions**.
6. **Alerts** — show delivery risk, follow-up, vendor escalation, and schedule impact items.

---

## Key Metrics To Mention Live

**ML baseline (synthetic holdout):**

- ~**75%** delay-risk classification accuracy
- ~**1.20-day** expected-delay regression MAE

**Dashboard (live demo data):**

- Open purchase orders and high-risk delivery count
- Vendor on-time rate and high-risk supplier count
- Schedule impact: On Track / Float Consumed / Critical Path Blocked
- Critical alerts by project phase
- POs needing follow-up before due date (e.g., PO-2133, PO-2179, PO-2125, PO-2008)

---

## Judging Narrative

**Hook:** Procurement is where construction delays start — but teams still run it from fragmented documents and spreadsheets.

**Insight:** You cannot fix schedule slippage with chat alone. You need **cited project knowledge**, **quantified risk**, and **actionable workflows** in one place.

**Proof:** SiteSage combines:

```text
RAG (cited document intelligence)
  + ML (75% risk-class baseline, ~1.2-day delay MAE on synthetic holdout)
  + Vendor risk scoring
  + Schedule impact mapping
  → Procurement alerts a PM can act on today
```

**Close:** SiteSage is a procurement copilot that helps managers **see risk early, trust the evidence, and act before the site stops**.

---

## One-Minute Pitch (spoken script)

> Procurement delays are one of the hidden drivers of construction schedule slippage. Teams find out too late because purchase orders, vendor commitments, and delivery status are scattered across spreadsheets, contracts, and emails.
>
> **SiteSage AI** fixes that with a local procurement command center. Teams upload project documents and ask questions in plain language — our **retrieval-augmented generation** pipeline answers with **cited evidence**, not guesses.
>
> On top of that, a **machine-learning baseline** — about **seventy-five percent** held-out accuracy on delay-risk classification and roughly **one-point-two days** mean error on delay duration — scores open deliveries, forecasts **expected ROJ dates**, and ranks **vendor reliability**.
>
> We then map delays to **schedule impact** — whether a slip consumes phase float or blocks the critical path — and generate **actionable procurement alerts**: what to escalate, what to follow up, and what threatens the lookahead.
>
> In the demo, SiteSage flags at-risk deliveries like **PO-2133**, high-risk vendors like **Badlands Components LLC**, and materials that can affect the **Foundation and Superstructure** schedule — with citations judges can verify live.
>
> SiteSage aligns with Kaya's vision: learn project context, predict what goes wrong, and help managers **act before delays hit the site**.

*Delivery tip: pause after "cited evidence" and after the ML metrics line so judges can absorb the numbers.*

---

## Likely Judge Questions

### Is this just a chatbot?

No. RAG is one layer. The prototype also runs **delay prediction**, **vendor risk scoring**, **schedule impact mapping**, and **alert generation** in a construction procurement workflow.

### Does it need internet?

No. The demo is **local-first**. Ollama is optional; the app still returns **cited extractive answers** from indexed documents without it.

### Is the data real?

The current build uses **synthetic procurement data** (`procurement_master.csv`) and aligned sample documents. The architecture supports swapping in real POs, contracts, and delivery history.

### Are the ML metrics production-ready?

No. **~75% classification accuracy** and **~1.20-day regression MAE** are **baseline results on synthetic holdout data** from our training pipeline. Production would need real project history, retraining, and monitoring.

### How does schedule impact work?

The prototype uses **phase-level float heuristics** (On Track / Float Consumed / Critical Path Blocked), not a full Primavera integration. See `procurement_scheduling_glossary.md`.

### Why local LLM instead of cloud?

Construction procurement data is sensitive. Local inference reduces exposure and fits a **Windows laptop demo** environment.

---

## Slide Bullets (optional deck)

- Problem: procurement chaos → late schedule impact
- Solution: SiteSage AI — local procurement copilot
- RAG: cited answers from project documents
- ML: 75% risk-class baseline · 1.20-day delay MAE (synthetic holdout)
- Vendor risk + schedule impact mapping + alerts
- Demo: PO-2133 · Badlands Components LLC · live citations
- Kaya fit: context → prediction → action
