# Hackathon Winning Plan

## Purpose

This file turns the Kaya AI IIT India Hackathon brief into concrete improvements for the current SiteSage AI app.

The current app is already a strong procurement-track prototype because it has:

- Document upload and indexing.
- Cited RAG answers.
- Delay risk prediction.
- Vendor reliability scoring.
- Procurement alerts.
- A Streamlit dashboard for demo flow.

To compete strongly, we should now make the app feel less like a generic AI dashboard and more like an expert procurement analyst that understands construction workflows, predicts schedule impact, and helps teams take action.

## What The Hackathon Brief Rewards

The `hackathon.md` brief makes three things clear:

- The project should solve a real construction problem, not only wrap an API call.
- Winning teams should combine multiple AI techniques.
- Procurement and supply chain tracks reward systems that answer:
  - What has been approved?
  - What is being fabricated?
  - What is delayed?
  - Where is it now?
  - Will it arrive when the project needs it?

For SiteSage AI, the winning angle should be:

> A local-first construction procurement copilot that reads project procurement documents, extracts order intelligence, predicts delivery and vendor risk, maps risk to schedule impact, and turns warnings into action workflows.

## Highest Impact Improvements

### 1. Add A Procurement Command Center Home Page

Current state:

- Overview shows KPIs, delivery risk chart, top alerts, and open orders.

What to improve:

- Make the first screen tell the full procurement risk story in 10 seconds.
- Add a "Today needs action" section with the top 3 issues.
- Add cards for:
  - Critical materials at risk.
  - Vendors needing escalation.
  - POs needing follow-up.
  - Estimated schedule impact days.
- Add filters for project phase, material category, vendor, and priority.

Why it helps win:

- Judges immediately understand the value.
- It feels like a procurement control tower, not a data table.

Owner:

- Member 1 with support from Member 2.

Priority:

- Must build.

### 2. Add Document Intelligence Extraction

Current state:

- Documents are chunked and searched.
- The app answers with citations.

What to improve:

- Extract structured fields from uploaded POs, contracts, and reports:
  - PO number.
  - Vendor.
  - Material.
  - Quantity.
  - Promised delivery date.
  - Expected ROJ date.
  - Payment terms.
  - Liquidated damages or penalty clause.
  - Escalation contact.
- Show an "Extracted Procurement Facts" table after upload.
- Store extracted facts in SQLite.
- Let the RAG answer cite both document chunks and extracted fields.

Why it helps win:

- The hackathon brief explicitly values document intelligence beyond basic OCR.
- It proves the app can turn messy documents into procurement data.

Owner:

- Member 3 builds extraction logic.
- Member 1 shows extracted facts in the upload page.
- Member 2 expands sample documents with realistic fields.

Priority:

- Must build.

### 3. Add Schedule Impact Mapping

Current state:

- Alerts say critical materials may affect schedule.
- Delay prediction gives expected ROJ date.

What to improve:

- Add a simple schedule dependency table:
  - Material.
  - Project phase.
  - Dependent site activity.
  - Required-on-site date.
  - Float days.
  - Impact if late.
- Compare expected ROJ date against required-on-site date.
- Show schedule impact:
  - No impact.
  - Consumes float.
  - Blocks activity.
  - Critical path risk.
- Add a chart showing impacted activities by phase.

Why it helps win:

- Construction procurement matters because delays hit site progress.
- This turns ML output into construction business impact.

Owner:

- Member 3 builds logic.
- Member 2 defines realistic dependencies.
- Member 1 adds visualization.

Priority:

- Must build.

### 4. Add What-If Mitigation Simulator

Current state:

- The app recommends actions but does not simulate alternatives.

What to improve:

- Add a "What if?" panel for high-risk orders:
  - Expedite transport.
  - Switch to backup vendor.
  - Split quantity between vendors.
  - Accept partial delivery.
  - Re-sequence activity.
- Show estimated result:
  - New expected ROJ date.
  - Reduced risk score.
  - Cost or operational tradeoff.
  - Recommended option.

Why it helps win:

- Forecasting plus optimization is called out in the hackathon brief.
- It moves the app from warning system to decision support.

Owner:

- Member 3 builds scoring rules.
- Member 1 adds UI.
- Member 2 validates construction realism.

Priority:

- Should build if time allows after the first three items.

### 5. Add Agentic Follow-Up Workflow

Current state:

- Alerts contain recommended actions.

What to improve:

- Add a button on each alert:
  - Draft vendor follow-up email.
  - Draft escalation note to procurement manager.
  - Create internal action item.
  - Mark alert as acknowledged or resolved.
- Use document context and risk data to generate the message.
- Keep actions local and demo-safe. Do not actually send emails.

Why it helps win:

- The brief rewards agentic systems that retrieve documents, take actions, and complete workflows.
- A drafted vendor escalation email is very demo-friendly.

Owner:

- Member 1 builds button and state.
- Member 3 builds draft generation.
- Member 2 checks tone and procurement correctness.

Priority:

- Should build.

### 6. Improve RAG Trust And Evaluation

Current state:

- RAG cites document chunks.
- Unsupported questions are declined.

What to improve:

- Add visible source cards with:
  - Document name.
  - Chunk ID.
  - Retrieved text excerpt.
  - Similarity score or confidence label.
- Add a small RAG evaluation file for demo questions.
- Add tests that verify all demo questions return expected citations or a decline.
- Add a "Why this answer?" expander in the AI Agent page.

Why it helps win:

- Judges will trust the answer more when evidence is visible.
- It prevents the app from looking like a normal chatbot.

Owner:

- Member 3 for retrieval and tests.
- Member 1 for UI.

Priority:

- Must build for credibility.

### 7. Add Vendor 360 View

Current state:

- Vendor page shows risk score, on-time rate, average delay, and recommendations.

What to improve:

- Add drill-down for each vendor:
  - Open POs.
  - Delayed POs.
  - Materials supplied.
  - Quality issues.
  - Communication score.
  - Contract clauses from documents.
  - Suggested negotiation or escalation strategy.
- Add a vendor comparison chart.
- Add "backup vendor suggestion" using vendors that supply the same category with lower risk.

Why it helps win:

- Procurement is about vendor relationships, not just delivery dates.
- This creates a stronger business story.

Owner:

- Member 3 builds scoring and backup logic.
- Member 1 builds drill-down UI.
- Member 2 validates vendor scenarios.

Priority:

- Should build.

### 8. Add CSV Upload To Update Procurement Data

Current state:

- Document upload exists.
- Structured procurement data comes from the sample CSV.

What to improve:

- Let users upload a procurement CSV.
- Validate required columns.
- Show errors for missing fields.
- Refresh delay, vendor, and alert pages from the uploaded data.
- Keep sample data as fallback.

Why it helps win:

- It proves the app can adapt to a real project dataset.
- It makes the demo more credible than fixed synthetic data only.

Owner:

- Member 1 and Member 3.

Priority:

- Should build if time allows.

### 9. Add Realistic Construction Data Pack

Current state:

- Sample data and two documents exist.

What to improve:

- Add more sample files:
  - Vendor update email.
  - Delivery tracker export.
  - Material inspection report.
  - Contract clause excerpt.
  - Project lookahead schedule.
- Add procurement rows for:
  - Structural steel.
  - Cement.
  - MEP cables.
  - HVAC equipment.
  - Transformer or generator package.
  - Formwork.
  - Safety equipment.
- Make the documents and CSV agree with each other.

Why it helps win:

- Better data makes every AI feature look more realistic.
- Judges can ask follow-up questions and the app will have context.

Owner:

- Member 2.

Priority:

- Must build.

### 10. Add Submission Assets Inside The Repo

Current state:

- Team docs include brief, demo script, pitch, roadmap, and architecture.

What to improve:

- Add a `submission/` or `doc_for_team/submission_pack.md` file with:
  - Project story.
  - Built with list.
  - Track selection.
  - 2-minute video script.
  - 10-slide deck outline.
  - Public project page copy.
  - Screenshots checklist.

Why it helps win:

- Stage 1 asks for proposal, slide deck, video, team info, and public project page content.
- Preparing these early reduces last-minute quality loss.

Owner:

- Member 2 leads.
- All members contribute.

Priority:

- Must build before submission.

## Recommended Build Order

### Sprint 1: Make The Demo Stronger

Build these first:

1. Procurement Command Center home page.
2. Realistic construction data pack.
3. RAG source cards and demo-question evaluation tests.
4. Document intelligence extraction table.

Expected result:

- The app looks polished.
- The assistant is visibly grounded.
- The data feels construction-specific.

### Sprint 2: Make The Product Smarter

Build these next:

1. Schedule impact mapping.
2. Vendor 360 view.
3. CSV upload for structured procurement data.

Expected result:

- The app connects procurement delays to project impact.
- Vendor risk becomes actionable.
- The prototype looks adaptable to real data.

### Sprint 3: Make It Feel Like An AI Agent

Build these if time remains:

1. What-if mitigation simulator.
2. Draft vendor follow-up or escalation message.
3. Alert acknowledgement and resolution state.

Expected result:

- The app does not just answer questions.
- It recommends, simulates, and prepares actions.

## Best Final Demo Story

Use this sequence:

1. "Construction procurement teams discover risk too late."
2. Upload POs, contracts, emails, and tracker files.
3. SiteSage extracts procurement facts.
4. Ask: "What is the expected ROJ date for steel?"
5. Show cited answer and retrieved source.
6. Show delay prediction for structural steel.
7. Show schedule impact: superstructure activity may be blocked.
8. Show vendor risk: ABC Metals needs escalation.
9. Show alerts: exact follow-up actions.
10. Show drafted vendor escalation email or what-if mitigation.

The final line should be:

> SiteSage does not replace the procurement manager. It gives them an expert analyst watching every order, vendor, and document 24/7.

## What Not To Spend Time On

Avoid these unless the core demo is already excellent:

- Full authentication.
- Production-grade user roles.
- Complex cloud deployment.
- Fine-tuning a large model.
- A large custom frontend rewrite.
- Real email sending.
- Too many unrelated tracks.

The app should stay focused on the procurement and supply chain tracks.

## Minimum Winning Feature Set

If time is limited, build only these:

1. Strong command center overview.
2. More realistic sample data and documents.
3. Extracted procurement facts from documents.
4. RAG source cards with clear citations.
5. Schedule impact mapping.
6. Vendor escalation draft from an alert.
7. Clean submission pack for proposal, deck, and video.

This set directly matches the hackathon guidance:

- Document intelligence.
- Forecasting.
- Construction-specific AI.
- Agentic workflow.
- Real procurement problem.

## Success Checklist

Before submission, confirm:

- App runs locally from the repo root.
- Sample documents index successfully.
- All demo questions return grounded answers or correct declines.
- Delay prediction shows expected ROJ date and risk drivers.
- Vendor risk shows high-risk vendors and why they are risky.
- Alerts show action, severity, due date, and linked material or PO.
- At least one alert can generate a vendor follow-up draft.
- Schedule impact is visible for critical materials.
- README setup commands are correct.
- The 2-minute video script matches the actual app.
- The deck explains problem, solution, AI techniques, demo flow, and future roadmap.
