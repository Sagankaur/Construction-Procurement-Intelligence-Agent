# SiteSage AI Brief

Status: local hackathon prototype  
Date: June 15, 2026

## One-Line Description

SiteSage AI is a construction procurement intelligence copilot that helps project managers detect material delivery delays, vendor reliability risks, and purchase order follow-ups from documents and structured procurement data.

## Problem

Large construction projects depend on many vendors, purchase orders, inspections, dispatches, and site-required delivery dates. Teams often discover delays late because procurement status is spread across contracts, purchase orders, spreadsheets, emails, and phone updates.

A single critical material delay, such as structural steel or a generator package, can affect the site schedule and push downstream work.

## Solution

SiteSage AI combines five capabilities in one local Streamlit dashboard:

- Document upload and chunking for procurement files.
- RAG-based question answering with cited document chunks.
- Delivery delay risk prediction.
- Vendor reliability scoring.
- Procurement alerts with recommended actions.

The app is not just a generic chatbot. It is shaped around construction procurement workflows: open purchase orders, ROJ dates, delayed materials, high-risk vendors, schedule impact, and follow-up actions.

## Target Users

- Project managers
- Procurement managers
- Planning engineers
- Site coordinators
- Commercial/vendor management teams

## Current Prototype Scope

Implemented in `code/`:

- Streamlit frontend with six pages.
- SQLite storage for uploaded document text and chunks.
- FAISS retrieval over stored chunks.
- Optional Ollama local LLM call.
- Deterministic cited fallback answer when Ollama is unavailable.
- Scikit-learn delay risk model trained from synthetic sample data.
- Vendor risk scoring from delivery, communication, and quality signals.
- Alert generation for critical materials, delivery risk, and vendor escalation.
- Backend tests covering RAG, unsupported questions, delay prediction, vendor risk, and alerts.

## Demo Data

The prototype includes synthetic procurement data for a construction project:

- Structural Steel from ABC Metals.
- MEP Copper Cables from ElectroPro Systems.
- Fire Rated Doors from SafeEntry Doors.
- Diesel Generator from PowerCore Equipments.
- Other concrete, facade, plumbing, elevator, waterproofing, and cement orders.

Sample documents are in `code/docs/`, and sample structured procurement history is in `code/data/sample_procurement_data.csv`.

## Why This Fits Kaya AI

Kaya's Amber concept is about learning project context and helping teams make decisions. SiteSage does this for procurement:

- Learns project context from uploaded procurement documents.
- Retrieves grounded evidence with citations.
- Predicts future risk before delays become site issues.
- Turns risk into clear manager actions.

## Success Criteria For The Hackathon Demo

- A judge can open the dashboard locally.
- A team member can load sample documents.
- The AI agent can answer demo questions with citations.
- Delay Prediction shows risk score, risk level, expected delay days, and expected ROJ date.
- Vendor Risk ranks risky vendors with explanations.
- Alerts page gives actionable procurement follow-ups.
