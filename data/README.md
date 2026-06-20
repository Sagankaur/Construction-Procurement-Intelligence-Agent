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

## Modeling Handoff

The data owner should produce:

- `data/processed/procurement_master.csv`
- `data/processed/vendor_master.csv` when vendor-level features are separated
- `data/processed/material_price_signals.csv` when commodity or WPI signals are added
- `models/model_report.md` with metrics, assumptions, and known limitations

Do not replace the demo fallback until the processed file has passed the app tests and a manual dashboard run.
