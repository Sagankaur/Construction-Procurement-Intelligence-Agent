# Procurement Scheduling Glossary

This document defines how SiteSage AI uses construction procurement scheduling terms in the **current prototype**. Definitions below match application behavior in `src/delay_model.py`, `src/schedule_impact.py`, `src/alerts.py`, and the Streamlit dashboard.

For a quick reference during demos, see also the **Key Reference Data** table in `demo_script.md`.

---

## Promised Delivery Date

**Construction meaning:** The date the vendor contractually commits to deliver material to the project delivery point (site, laydown area, or nominated location). Procurement teams track this for follow-up, dispatch confirmation, and vendor performance.

**In SiteSage:**

| Aspect | Detail |
| --- | --- |
| Field | `promised_delivery_date` |
| Legacy CSV | Stored explicitly per purchase order |
| Processed CSV | Synthesized as `today + days_until_promised_delivery` when rows are loaded |
| Delay Prediction form | User-entered **Promised Delivery Date** |
| Open-order tables | Shown as **Promised Date** |
| Follow-up alerts | Used as `due_date` for orders due within 7 days |

**Operational note:** Promised delivery is the baseline commitment. It is **not** the same as the date material is required for installation (see ROJ below).

---

## Required On-Site (ROJ) Date

**Construction meaning:** In live projects, **ROJ** (Required On-Site / Required on Job) is the date a material must be physically available on site for the dependent construction activity (e.g., steel erection, MEP rough-in). It usually comes from the project lookahead or master schedule and may be **earlier or stricter** than the vendor’s promised delivery date.

**In SiteSage (prototype simplification):**

SiteSage does **not** currently store a separate schedule-driven “required ROJ” column from Primavera or MS Project. Instead it uses **Expected ROJ Date** as a **forecast of when material will actually be on site after predicted delay**.

| Aspect | Detail |
| --- | --- |
| Field | `expected_roj_date` |
| Formula (ML prediction) | `promised_delivery_date + expected_delay_days` |
| Formula (processed CSV load) | `promised_delivery_date + actual_delay_days` (training label used as proxy) |
| Delivery risk table | From batch ML inference on open orders |
| RAG documents | Stated explicitly (e.g., structural steel ROJ linked to PO-2133) |

**UI labeling:** The Delay Prediction page timeline labels this milestone **Est. Delivery**; open-order tables use **Predicted Delivery**. Alerts and backend fields use **expected ROJ**. All refer to the same computed forecast date in the prototype.

**Operational note:** Treat **Expected ROJ** as “forecast on-site availability after procurement delay risk,” not as the contractual schedule requirement imported from a CPM tool.

---

## Expected Delay

**Construction meaning:** The number of calendar days a delivery is expected to slip beyond the promised delivery date before material is available for site use. Used for risk briefings, vendor escalation, and schedule what-if conversations.

**In SiteSage:**

| Aspect | Detail |
| --- | --- |
| Field | `expected_delay_days` |
| Source | `RandomForestRegressor` output, combined with risk score: `max(0, regressor_output, risk_score / 12 - 2)` |
| Delay Prediction UI | **Expected Lead-Time Delay** (days) |
| Overview KPI | Sum of `expected_delay_days` across open high-risk deliveries → **estimated cumulative schedule delay** (days) |

**Distinct from other delay fields:**

| Field | Meaning in prototype |
| --- | --- |
| `expected_delay_days` | ML forecast used in Delay Prediction, delivery risk table, and Overview cumulative delay KPI |
| `actual_delay_days` | Label in processed CSV / days delivered after promise for closed orders |
| `observed_delay_days` | Derived open-order overdue days + actual delay for delivered rows |
| `delay_days` (schedule impact table) | Uses `actual_delay_days`, or `observed_delay_days` for open orders — **not** `expected_delay_days` |

**Operational note:** Expected delay answers “how many days past promise do we forecast?” Schedule impact mapping (below) uses dataset delay fields, not the ML forecast, unless those fields align by construction in synthetic data.

---

## Schedule Impact

**Construction meaning:** Whether a procurement delay will affect the project schedule — consuming activity **float** or **blocking the critical path** — for the phase that depends on the material.

**In SiteSage (two related mechanisms):**

### A. Schedule impact mapping (`src/schedule_impact.py`)

Used on the **Overview** page (Critical Path Blocked / Float Consumed / On Track chart).

| Input | Detail |
| --- | --- |
| Delay used | `actual_delay_days`, or `observed_delay_days` when the order is still open |
| Float budget | Phase-specific calendar days (`PHASE_FLOAT`): Foundation 5, Superstructure 3, MEP Fitouts 2, Finishes 7, etc. |
| Unlisted phases | Default float = 4 days |

| Status | Rule |
| --- | --- |
| On Track | `delay_days <= 0` |
| Float Consumed | `0 < delay_days <= phase_float` |
| Critical Path Blocked | `delay_days > phase_float` |

`float_remaining = max(0, phase_float - delay_days)`.

This is a **phase-level float heuristic** for demo storytelling. It does **not** read a full CPM network or compare Expected ROJ to a schedule activity date.

### B. Schedule Impact alerts (`src/alerts.py`)

Separate rule: **Critical** severity when `criticality` is Critical (or High in legacy data) **and** `current_status` is At Risk or Delayed. These alerts flag materials that **may** affect the schedule; they do not run the float table logic.

### C. Overview executive copy

The narrative **estimated cumulative schedule delay** sums ML `expected_delay_days` from the delivery risk table. That KPI is a **portfolio delay-day total**, not the same calculation as the float-consumption chart.

**Operational note:** All three are valid prototype views for a hackathon demo, but they answer slightly different questions. Use the glossary when presenting to judges to avoid conflating them.

---

## How Values Flow Through The Demo

```text
Purchase order
  promised_delivery_date          (vendor commitment)
        +
  expected_delay_days             (ML forecast)
        =
  expected_roj_date               (forecast on-site availability)

Parallel track:
  delay_days in schedule_impact   (dataset actual / observed delay)
        vs
  phase_float                     (Foundation, Superstructure, …)
        =>
  On Track | Float Consumed | Critical Path Blocked
```

---

## Real-World Alignment

| Term | Real-world practice | SiteSage prototype |
| --- | --- | --- |
| Promised delivery | Vendor PO / contract date | Supported |
| Required ROJ from schedule | Lookahead / activity need date | Not imported; documents may reference schedule dependencies in text |
| Expected delay | Forecast slip vs promise | Supported via ML |
| Float consumption | CPM float on tied activity | Approximated by phase float budgets |
| Critical path blocked | Delay exceeds total float on critical activity | Approximated when delay exceeds phase float |

---

## Known Prototype Limitations

1. **No schedule integration** — ROJ is forecast arrival, not Primavera/MSP required date.
2. **Multiple delay fields** — ML expected delay vs dataset delay used in schedule impact mapping.
3. **Phase name gaps** — `MEP Rough-In` and `MEP Fitouts` are both mapped to a 2-day float in `PHASE_FLOAT` to prevent fallback to the default 4-day float.
4. **UI label variance** — “Est. Delivery” / “Predicted Delivery” / “expected ROJ” refer to the same backend field in most flows.

These limitations are acceptable for the hackathon prototype and are called out in `roadmap_risks.md` for production next steps.
