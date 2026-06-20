# Sprint 1: Fix The Demo Foundation -> DONE
Make repo root the only active app path.
Update team docs that still mention code/.
Keep tests passing.
Add a short data/README.md explaining synthetic vs real data.

# Sprint 2: Data Pipeline, Your Main Ownership
Create:
data/raw/
data/processed/
models/
scripts/
Your deliverables:
data/processed/procurement_master.csv
data/processed/vendor_master.csv
data/processed/material_price_signals.csv
models/delay_risk_model.joblib
models/vendor_risk_model.joblib
models/model_report.md
Use Kaggle datasets for fast training, then enrich with official context:
India CPPP/eProcurement for tenders and bid awards: eProcure
GeM procurement scale/categories: GeM Statistics
Open Contracting public procurement datasets: OCP Data Registry
USAspending contract awards: USAspending API
India WPI/PPI material price signals: Office of Economic Adviser
World Bank commodity prices: World Bank Commodity Markets

# Sprint 3: Model Upgrade
Do not start with deep learning. Use strong tabular baselines:
XGBoost or RandomForest for delay risk class.
RandomForest/XGBoost regressor for expected delay days.
Vendor risk score from model + rules.
Add evaluation: F1, confusion matrix, MAE for delay days.
Winning metric story:
Our model combines vendor history, material category, contract value, priority, project phase, communication score, quality issues, lead time, and market price pressure to predict procurement delay risk.

# Sprint 4: Must-Build Product Features
Build these before fancy extras:
CSV Upload Updates Dashboard
User uploads procurement tracker; all risk pages refresh.

Ollama Extracted Procurement Facts
Upload PO/contract/email, show extracted fields in a table with source chunk.

RAG Source Cards
After every answer, show:
document name
chunk id
excerpt
relevance score

Schedule Impact Mapping
Add simple table:

material, project_phase, required_on_site_date, dependent_activity, float_days
Then show whether delay:
has no impact
consumes float
blocks activity
threatens critical path
Alert To Vendor Email
Button: Draft Follow-Up.
Ollama writes the email using PO, vendor, risk, due date, and citation.
Final Demo Flow
Use this exact story:
Open dashboard: “This is a procurement command center.”
Upload sample PO/vendor contract/email.
Ollama extracts PO facts.
Ask: “What is the expected ROJ date for steel?”
Show cited answer and source card.
Show delay model predicts Structural Steel risk.
Show schedule impact: Superstructure may be blocked.
Show vendor risk: ABC Metals high risk.
Show alert.
Click Draft Follow-Up and show Ollama-generated vendor escalation email.
That final click is important. It proves agentic workflow.
Your Next Steps
Clean and merge Kaggle datasets into the current app schema.
Add realistic construction-specific columns: project_phase, criticality, expected_roj_date, actual_delivery_date, quality_issues, communication_score.
Train baseline models and save them to models/.
Prepare a model report with metrics and limitations.
Coordinate with the app owner to load your processed CSV and model artifact.
Coordinate with backend owner to combine ML output + Ollama explanations.