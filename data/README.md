# SiteSage Data Workflow

This folder holds the procurement data used by the local prototype.

## Current Demo Data

- `sample_procurement_data.csv` is the stable synthetic fallback used by the dashboard, delay model, vendor risk scoring, and alerts.
- The current app expects this file to stay available with the existing column names.

## Working Folders

Use this convention for the data/model sprint:

```text
data/raw/        downloaded Kaggle, government, and company reference datasets
data/processed/  cleaned app-ready CSV files with normalized columns
models/          trained model artifacts and model reports
```

Large raw datasets should stay out of Git unless they are small curated demo samples.

## Target Processed Schema

Cleaned procurement rows should preserve or map into these app columns:

```text
po_number
material_name
category
vendor_name
order_date
promised_delivery_date
expected_roj_date
actual_delivery_date
quantity
unit
contract_value
priority
project_phase
criticality
current_status
quality_issues
communication_score
historical_on_time_rate
```

### Scheduling field semantics

See `doc_for_team/procurement_scheduling_glossary.md` for full definitions. Short reference:

| Column | Meaning |
| --- | --- |
| `order_date` | Date the purchase order was placed |
| `promised_delivery_date` | Vendor-committed delivery date to the project delivery point |
| `expected_roj_date` | Forecast date material will be on site after delay (`promised + delay`). In processed loads, synthesized from `actual_delay_days` labels |
| `actual_delivery_date` | Date material was actually received (empty for open orders) |

Derived at runtime (not required in CSV):

- `expected_delay_days` — ML forecast from `delay_model.py`
- `observed_delay_days` — overdue days for open orders plus actual delay for closed orders
- Schedule impact status — from `schedule_impact.py` float comparison

Supporting columns for modeling:

```text
lead_time
days_until_promised_delivery
actual_delay_days
risk_level
```

## Modeling Handoff

The data owner should produce:

- `data/processed/procurement_master.csv`
- `data/processed/vendor_master.csv` when vendor-level features are separated
- `data/processed/material_price_signals.csv` when commodity or WPI signals are added
- `models/model_report.md` with metrics, assumptions, and known limitations

Do not replace the demo fallback until the processed file has passed the app tests and a manual dashboard run.
