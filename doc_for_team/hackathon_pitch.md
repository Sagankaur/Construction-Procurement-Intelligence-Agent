# Hackathon Pitch

## Pitch Title

SiteSage AI: Construction Procurement Intelligence Agent

## Elevator Pitch

Construction delays often start in procurement, but teams notice them too late. SiteSage AI acts as a procurement copilot that reads project documents, answers with citations, predicts material delivery delay risk, ranks vendor reliability, and generates action-ready alerts for project managers.

## Problem

Project teams lose time because procurement information is fragmented:

- Purchase orders are in spreadsheets.
- Vendor commitments are in contracts.
- Status updates are in emails and calls.
- Delay risk is tracked manually.
- Critical material issues surface late.

This creates avoidable schedule impact.

## Solution

SiteSage AI creates a single local dashboard for procurement intelligence:

- Upload procurement documents.
- Ask natural-language questions.
- Get cited answers from project documents.
- Predict delivery delay risk.
- Score vendor reliability.
- Generate critical alerts and follow-up actions.

## Why It Is Different

Many teams will build a document chatbot. SiteSage goes beyond that:

- It combines RAG with predictive risk.
- It uses construction-specific entities: PO, vendor, material, ROJ date, project phase, criticality.
- It turns answers into operational alerts.
- It can run locally with optional Ollama inference.

## Kaya AI Alignment

Kaya's Amber idea is about learning project context and helping teams make decisions. SiteSage applies that to construction procurement:

- It learns from project documents.
- It understands procurement risk context.
- It predicts risk from historical signals.
- It recommends actions for project managers.

## Target Persona

Primary user:

- Project manager responsible for schedule and procurement coordination.

Secondary users:

- Procurement manager
- Planning engineer
- Site engineer
- Vendor management team

## Demo Proof Points

During the demo, show:

- Sample procurement documents loaded into the system.
- AI answer with citation for expected ROJ date for steel.
- Delay risk prediction for structural steel from ABC Metals.
- Vendor risk chart showing high-risk suppliers.
- Alerts that identify critical materials and follow-up actions.

## Key Metrics To Mention

Prototype metrics are synthetic, but the product direction can track:

- Number of open purchase orders.
- Percentage of high-risk deliveries.
- Vendor on-time rate.
- Average expected delay days.
- Critical alerts by project phase.
- Follow-up closure time.

## Judging Narrative

SiteSage is valuable because it connects three layers:

1. Project knowledge from documents.
2. Predictive intelligence from procurement data.
3. Action workflow through alerts.

That makes it closer to a real construction intelligence assistant than a standalone chatbot.

## One-Minute Pitch

> Procurement delays are one of the hidden causes of construction schedule slippage. Teams often find out too late because status is buried across POs, contracts, spreadsheets, and vendor updates. SiteSage AI solves this by acting as a local procurement copilot. It lets teams upload documents, ask questions with cited answers, predict delivery delay risk, score vendor reliability, and generate alerts for critical materials. In our demo, SiteSage identifies at-risk steel, high-risk vendors, purchase orders needing follow-up, and materials that may affect the project schedule. It aligns with Kaya's vision because it learns project context and helps managers make decisions before delays hit the site.

## Likely Judge Questions

### Is this just a chatbot?

No. The chatbot is only one interface. The prototype also has delay prediction, vendor scoring, alerts, and a dashboard built around construction procurement workflows.

### Does it need internet?

No. The demo is local-first. Ollama is optional. The fallback answer mode still returns cited answers from indexed documents.

### Is the data real?

The current prototype uses synthetic construction procurement data. The architecture is designed so real purchase orders, vendor contracts, schedules, and procurement reports can replace the sample data.

### Is the ML model production-ready?

No. It is a hackathon prototype model showing the risk-scoring workflow. Production use would need historical project data, validation, calibration, and monitoring.

### Why local LLM instead of cloud?

Construction project data can be sensitive. Local inference reduces data exposure and fits the target Windows laptop environment.
