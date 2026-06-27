**Sprint 1: Fix The Demo Foundation** -> DONE
- Make repo root the only active app path.
- Update team docs that still mention `code/`.
- Keep tests passing.
- Add a short `data/README.md` explaining synthetic vs real data.

**Sprint 2: Data Pipeline, Your Main Ownership**
Create:

```text
data/raw/
data/processed/
models/
scripts/
```

Your deliverables:

```text
data/processed/procurement_master.csv
data/processed/vendor_master.csv
data/processed/material_price_signals.csv
models/delay_risk_model.joblib
models/vendor_risk_model.joblib
models/model_report.md
```

Use Kaggle datasets for fast training, then enrich with official context:

 https://www.kaggle.com/datasets/shahriarkabir/procurement-kpi-analysis-dataset?utm_source=chatgpt.com

 https://www.kaggle.com/datasets/shfarshid/supplier-stability-dataset-for-procurement?utm_source=chatgpt.com

 https://www.kaggle.com/datasets/ayodejiibrahimlateef/supply-chain-datasets?utm_source=chatgpt.com

- India CPPP/eProcurement for tenders and bid awards: [eProcure](https://eprocure.gov.in/eprocure/app)
- GeM procurement scale/categories: [GeM Statistics](https://gem.gov.in/statistics)
- Open Contracting public procurement datasets: [OCP Data Registry](https://data.open-contracting.org/)
- USAspending contract awards: [USAspending API](https://api.usaspending.gov/)
- India WPI/PPI material price signals: [Office of Economic Adviser](https://eaindustry.nic.in/)
- World Bank commodity prices: [World Bank Commodity Markets](https://www.worldbank.org/en/research/commodity-markets)

DONE->
data/processed/procurement_master.csv (Enriched with construction logic)
data/processed/vendor_master.csv (Aggregated reliability profiles)
data/processed/material_price_signals.csv (Macro market indicators)
models/delay_risk_classifier.joblib (Trained risk engine)
models/delay_risk_regressor.joblib (Trained duration engine)
models/model_report.md (Performance report)

**Sprint 3: Model Upgrade**
Do not start with deep learning. Use strong tabular baselines:

- XGBoost or RandomForest for delay risk class.
- RandomForest/XGBoost regressor for expected delay days.
- Vendor risk score from model + rules.
- Add evaluation: F1, confusion matrix, MAE for delay days.

Winning metric story:

> Our model combines vendor history, material category, contract value, priority, project phase, communication score, quality issues, lead time, and market price pressure to predict procurement delay risk.

**Sprint 4: Must-Build Product Features**
Build these before fancy extras:

1. **CSV Upload Updates Dashboard**  
   User uploads procurement tracker; all risk pages refresh.

2. **Ollama Extracted Procurement Facts**  
   Upload PO/contract/email, show extracted fields in a table with source chunk.

3. **RAG Source Cards**  
   After every answer, show:
   - document name
   - chunk id
   - excerpt
   - relevance score

4. **Schedule Impact Mapping**  
   **Implemented (prototype):** `src/schedule_impact.py` compares dataset delay days to per-phase float budgets (On Track / Float Consumed / Critical Path Blocked). See `procurement_scheduling_glossary.md`.

   **Future enhancement:** tie to schedule activities:

```text
material, project_phase, required_on_site_date, dependent_activity, float_days
```

Then show whether delay:
- has no impact
- consumes float
- blocks activity
- threatens critical path

5. **Alert To Vendor Email**  
   Button: `Draft Follow-Up`.  
   Ollama writes the email using PO, vendor, risk, due date, and citation.

**Final Demo Flow**
Use this exact story:

1. Open dashboard: “This is a procurement command center.”
2. Upload sample PO/vendor contract/email.
3. Ollama extracts PO facts.
4. Ask: “What is the expected ROJ date for steel?”
5. Show cited answer and source card.
6. Show delay model predicts Structural Steel risk.
7. Show schedule impact: Superstructure may be blocked.
8. Show vendor risk: ABC Metals high risk.
9. Show alert.
10. Click `Draft Follow-Up` and show Ollama-generated vendor escalation email.

That final click is important. It proves agentic workflow.

**Your Next Steps**
1. Clean and merge Kaggle datasets into the current app schema.
2. Add realistic construction-specific columns: `project_phase`, `criticality`, `expected_roj_date`, `actual_delivery_date`, `quality_issues`, `communication_score`.
3. Train baseline models and save them to `models/`.
4. Prepare a model report with metrics and limitations.
5. Coordinate with the app owner to load your processed CSV and model artifact.
6. Coordinate with backend owner to combine ML output + Ollama explanations.

