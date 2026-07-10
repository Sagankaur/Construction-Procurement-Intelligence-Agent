import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import math

from src.alerts import alert_counts, generate_alerts
from src.delay_model import get_delivery_risk_table, load_procurement_data
from src.schedule_impact import get_schedule_impact_table, schedule_impact_summary
from src.vendor_risk import get_vendor_risk_table


# ---------------------------------------------------------------------------
# Cached data loaders
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def _cached_procurement_data():
    return load_procurement_data()


@st.cache_data(ttl=300, show_spinner=False)
def _cached_delivery_risk():
    return get_delivery_risk_table()


@st.cache_data(ttl=300, show_spinner=False)
def _cached_vendor_risk():
    return get_vendor_risk_table(load_procurement_data())


# ---------------------------------------------------------------------------
# Helper functions for rendering and custom charts
# ---------------------------------------------------------------------------
def render_clean_html(html_str):
    """Split by lines, strip whitespace, join back, remove empty lines and render natively via st.html to prevent markdown code blocks."""
    clean_lines = [line.strip() for line in html_str.splitlines() if line.strip()]
    st.html("".join(clean_lines))


def generate_plotly_gauge(health):
    """Generate a premium modern progress gauge chart with stacked annotations."""
    if health <= 20:
        color = "#EF4444"
        status = "CRITICAL"
    elif health <= 40:
        color = "#F59E0B"
        status = "POOR"
    elif health <= 60:
        color = "#FCD34D"
        status = "FAIR"
    elif health <= 80:
        color = "#34D399"
        status = "GOOD"
    else:
        color = "#10B981"
        status = "EXCELLENT"

    is_dark = st.session_state.get("theme", "light") == "dark"
    gauge_bg = "#334155" if is_dark else "#F1F5F9"
    tick_color = "#94A3B8" if is_dark else "#64748B"
    text_color = "#FFFFFF" if is_dark else "#1E3A5F"

    fig = go.Figure(go.Indicator(
        mode="gauge",
        value=health,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100], 'visible': True, 'tickmode': 'array', 'tickvals': [0, 20, 40, 60, 80, 100], 'ticktext': ['0', '20', '40', '60', '80', '100'], 'tickfont': {'color': tick_color, 'size': 8}},
            'bar': {'color': color, 'thickness': 0.8},
            'bgcolor': gauge_bg,
            'borderwidth': 0,
        }
    ))
    
    # Render stacked value and status label using a single HTML text block
    fig.add_annotation(
        x=0.5,
        y=0.3,
        text=f"<span style='font-size: 28px; color: {text_color}; font-weight: bold;'>{health}%</span><br><span style='font-size: 11px; color: {color}; font-weight: bold;'>{status}</span>",
        showarrow=False,
        align="center",
        xref="paper",
        yref="paper"
    )

    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=10),
        height=130,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, sans-serif")
    )
    return fig


def get_impact_status(row) -> str:
    crit = str(row.get("criticality", "")).lower()
    lvl = str(row.get("risk_level", "")).lower()
    if lvl == "high":
        return "Critical" if crit == "high" else "High"
    if lvl == "medium":
        return "Medium"
    return "Low"


def _procurement_health_score(delivery_risk, vendor_risk, counts):
    """Compute an overall procurement health score (0-100)."""
    if delivery_risk.empty:
        return 85  # Default healthy

    high_risk_items = (delivery_risk["risk_level"] == "High").sum()
    high_risk_vendors = (vendor_risk["risk_level"] == "High").sum()
    critical_alerts = counts.get("Critical", 0)

    # Score penalises risk proportionally
    score = 100
    score -= min(high_risk_items * 8, 40)
    score -= min(high_risk_vendors * 6, 20)
    score -= min(critical_alerts * 5, 20)
    score -= min((delivery_risk["risk_score"].mean() / 100) * 15, 15)
    return max(int(score), 5)


def main():
    # Inject Custom CSS for modern enterprise look and feel
    st.markdown(
        """
        <style>
        .overview-title-container {
            background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
            border: 1px solid #FFCC80;
            border-radius: 14px;
            padding: 1.5rem 1.8rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(255, 152, 0, 0.05);
        }
        .overview-title {
            font-size: 1.3rem !important;
            font-weight: 800 !important;
            color: #07315F !important;
            margin: 0 0 0.3rem 0 !important;
            line-height: 1.2 !important;
        }
        .overview-subtitle {
            font-size: 0.88rem !important;
            color: #4A5568 !important;
            opacity: 0.95 !important;
            margin: 0 !important;
        }

        /* Executive Summary Card */
        .exec-summary-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-left: 4px solid var(--primary-blue);
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
            margin-bottom: 2rem;
        }
        .exec-content {
            width: 100%;
        }
        .exec-title {
            font-size: 1rem;
            font-weight: 700;
            color: var(--primary-navy);
            margin-bottom: 0.25rem;
        }
        .exec-text {
            font-size: 0.88rem;
            color: var(--text-color);
            line-height: 1.5;
            margin: 0;
        }
        .exec-text b {
            color: var(--primary-navy);
            font-weight: 600;
        }

        /* KPI Card styling */
        .kpi-card-custom {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 0.8rem 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            height: 102px;
            box-sizing: border-box;
            margin-bottom: 2rem;
        }
        .kpi-card-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        .kpi-icon-box {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .kpi-label-box {
            display: flex;
            flex-direction: column;
        }
        .kpi-lbl {
            font-size: 0.65rem;
            font-weight: 700;
            color: var(--text-color);
            opacity: 0.75;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            line-height: 1.2;
        }
        .kpi-val {
            font-size: 1.35rem;
            font-weight: 800;
            color: var(--primary-navy);
            line-height: 1.1;
            margin-top: 0.15rem;
        }
        .kpi-cap {
            font-size: 0.75rem;
            color: var(--text-color);
            opacity: 0.8;
            margin: 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* AI Recommended Actions Card Styles */
        .ai-actions-container {
            width: 100%;
        }
        .ai-actions-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.25rem;
        }
        .ai-actions-header-left {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        .ai-logo-box {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            background-color: rgba(59, 130, 246, 0.08);
            color: #3B82F6;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            border: 1px solid rgba(59, 130, 246, 0.15);
        }
        .ai-actions-titles {
            display: flex;
            flex-direction: column;
            gap: 0.15rem;
        }
        .ai-actions-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--primary-navy);
            margin: 0;
        }
        .ai-actions-subtitle {
            font-size: 0.82rem;
            color: var(--text-color);
            opacity: 0.7;
            margin: 0;
        }
        .ai-actions-view-all {
            display: flex;
            align-items: center;
            gap: 0.35rem;
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-color);
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            padding: 0.4rem 0.75rem;
            border-radius: 6px;
            text-decoration: none;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
            transition: all 0.2s ease;
        }
        .ai-actions-view-all:hover {
            border-color: var(--primary-blue);
            background: rgba(79, 140, 255, 0.08);
        }
        .ai-actions-grid {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            margin-bottom: 1.25rem;
        }
        .ai-action-card {
            flex: 1;
            min-width: 220px;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1.25rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.01);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
            min-height: 180px;
            box-sizing: border-box;
            transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        }
        .ai-action-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            border-color: var(--primary-blue);
        }
        .ai-card-top {
            display: flex;
            gap: 0.75rem;
            align-items: flex-start;
            margin-bottom: 1rem;
        }
        .ai-card-num-box {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: rgba(148, 163, 184, 0.15);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .ai-card-num {
            font-size: 0.75rem;
            font-weight: 700;
            color: #64748B;
        }
        .ai-card-icon-wrapper {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background: #FFF5F5;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .ai-card-icon-wrapper-amber {
            background: #FFFBEB;
        }
        .ai-card-icon-wrapper-blue {
            background: #EFF6FF;
        }
        .ai-card-details {
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
        }
        .ai-card-title {
            font-size: 0.85rem;
            font-weight: 700;
            color: var(--primary-navy);
            line-height: 1.3;
            margin: 0;
        }
        .ai-card-desc {
            font-size: 0.78rem;
            color: var(--text-color);
            opacity: 0.8;
            line-height: 1.4;
            margin: 0;
        }
        .ai-card-bottom {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: auto;
            padding-top: 0.75rem;
            border-top: 1px dashed var(--border-color);
        }
        .badge-priority-high {
            font-size: 0.68rem;
            font-weight: 700;
            color: #EF4444;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }
        .badge-priority-medium {
            font-size: 0.68rem;
            font-weight: 700;
            color: #F59E0B;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }
        .badge-priority-low {
            font-size: 0.68rem;
            font-weight: 700;
            color: #10B981;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }
        .ai-card-due {
            font-size: 0.75rem;
            color: #64748B;
            opacity: 0.8;
            font-weight: 500;
        }
        .ai-actions-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 1rem;
            background: var(--bg-color);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            box-sizing: border-box;
        }
        .ai-actions-footer-left {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.78rem;
            color: #64748B;
        }
        .ai-actions-footer-right {
            display: flex;
            align-items: center;
            gap: 0.35rem;
            font-size: 0.75rem;
            color: #94A3B8;
            font-weight: 500;
        }

        /* Two-column layout elements */
        .col-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.25rem;
        }
        .col-card-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--primary-navy);
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }
        .col-card-link {
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--primary-blue);
            text-decoration: none;
        }
        .col-card-link:hover {
            text-decoration: underline;
        }

        /* Custom Table */
        .custom-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8rem;
        }
        .custom-table th {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 0.75rem 1rem;
            opacity: 0.5;
            font-weight: 700;
            border-bottom: 1px solid var(--border-color) !important;
            text-align: left;
            color: var(--text-color);
        }
        .custom-table td {
            padding: 0.85rem 1rem;
            border-bottom: 1px solid var(--border-color) !important;
            font-size: 0.82rem;
            color: var(--text-color);
            vertical-align: middle;
        }
        .custom-table tr {
            transition: background-color 0.15s ease;
        }
        .custom-table tr:hover {
            background-color: rgba(79, 140, 255, 0.03) !important;
        }
        .custom-table tr:last-child td {
            border-bottom: none !important;
        }
        .mat-cell {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            font-weight: 600;
            color: var(--text-color);
        }
        .vendor-cell {
            font-weight: 600;
            color: var(--text-color);
        }
        .prog-container {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .prog-bar {
            width: 40px;
            height: 4px;
            background-color: var(--border-color);
            border-radius: 2px;
            overflow: hidden;
        }
        .prog-fill {
            height: 100%;
            border-radius: 2px;
        }

        /* Badge severities */
        .badge-sev {
            display: inline-block;
            font-size: 0.68rem;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }
        .badge-sev-Critical, .badge-sev-critical {
            background-color: rgba(239, 68, 68, 0.08) !important;
            color: #EF4444 !important;
            border: 1px solid rgba(239, 68, 68, 0.15) !important;
        }
        .badge-sev-High, .badge-sev-high {
            background-color: rgba(245, 158, 11, 0.08) !important;
            color: #F59E0B !important;
            border: 1px solid rgba(245, 158, 11, 0.15) !important;
        }
        .badge-sev-Medium, .badge-sev-medium {
            background-color: rgba(79, 140, 255, 0.08) !important;
            color: #4F8CFF !important;
            border: 1px solid rgba(79, 140, 255, 0.15) !important;
        }
        .badge-sev-Low, .badge-sev-low {
            background-color: rgba(16, 185, 129, 0.08) !important;
            color: #10B981 !important;
            border: 1px solid rgba(16, 185, 129, 0.15) !important;
        }

        /* Alerts feed list */
        .alert-list-container {
            display: flex;
            flex-direction: column;
            gap: 0.65rem;
        }
        .alert-row-item {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-left: 3px solid var(--border-color);
            border-radius: 8px;
            padding: 0.85rem 1rem;
            transition: all 0.2s ease;
        }
        .alert-row-item:hover {
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
            border-color: #CBD5E1;
        }
        .alert-border-Critical, .alert-border-critical {
            border-left-color: #EF4444 !important;
        }
        .alert-border-High, .alert-border-high {
            border-left-color: #F59E0B !important;
        }
        .alert-border-Medium, .alert-border-medium {
            border-left-color: #4F8CFF !important;
        }
        .alert-border-Low, .alert-border-low {
            border-left-color: #10B981 !important;
        }
        .alert-item-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.35rem;
        }
        .alert-item-meta {
            font-size: 0.72rem;
            color: var(--text-color);
            opacity: 0.6;
            font-weight: 600;
        }
        .alert-item-title {
            font-size: 0.85rem;
            font-weight: 700;
            color: var(--text-color);
            margin-bottom: 0.45rem;
            line-height: 1.35;
        }
        .alert-item-dates {
            display: flex;
            justify-content: space-between;
            font-size: 0.72rem;
            color: var(--text-color);
            opacity: 0.65;
        }
        .alert-item-dates b {
            color: var(--text-color);
        }

        /* Bottom charts styling & containers */
        .chart-card-title {
            font-size: 0.9rem;
            font-weight: 700;
            color: var(--primary-navy);
            margin-bottom: 0.75rem;
        }

        /* Style Streamlit containers with border to match custom cards */
        div[data-testid="stVerticalBlockBorderContainer"],
        .stVerticalBlockBorderContainer,
        div[data-testid="column"] div[data-testid="stVerticalBlockBorderContainer"],
        div[data-testid="column"] .stVerticalBlockBorderContainer {
            background-color: var(--card-bg) !important;
            background: var(--card-bg) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 16px !important;
            padding: 1.5rem !important;
            box-shadow: 0 4px 12px rgba(15,23,42,0.04) !important;
            margin-bottom: 2rem !important;
            transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        div[data-testid="stVerticalBlockBorderContainer"]:hover,
        .stVerticalBlockBorderContainer:hover,
        div[data-testid="column"] div[data-testid="stVerticalBlockBorderContainer"]:hover,
        div[data-testid="column"] .stVerticalBlockBorderContainer:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 10px 20px rgba(15, 23, 42, 0.06), 0 4px 6px rgba(0, 0, 0, 0.01) !important;
            border-color: #CBD5E1 !important;
        }

        /* Trends Card Target styling using :has() selector - FORCES EQUAL HEIGHT AND FLEX DISTRIBUTION */
        div[data-testid="stVerticalBlockBorderContainer"]:has(.trends-card-marker) {
            background-color: var(--card-bg) !important;
            background: var(--card-bg) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 20px !important;
            padding: 32px !important;
            box-shadow: 0 10px 40px rgba(15, 23, 42, 0.08) !important;
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            min-height: 505px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
        }
        div[data-testid="stVerticalBlockBorderContainer"]:has(.trends-card-marker):hover {
            transform: translateY(-4px) !important;
            box-shadow: 0 20px 50px rgba(15, 23, 42, 0.12) !important;
            border-color: rgba(79, 140, 255, 0.4) !important;
        }

        /* Redesigned Trends Card Elements */
        .trend-card-header-new {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            margin-bottom: 0.25rem;
        }
        .trend-title-new {
            font-size: 0.98rem;
            font-weight: 700;
            color: var(--primary-navy);
            margin: 0;
            letter-spacing: -0.02em;
        }
        .trend-subtitle-new {
            font-size: 0.78rem;
            color: #64748B;
            margin: 0;
        }
        .trend-badge-new {
            font-size: 0.62rem;
            font-weight: 700;
            padding: 3px 7px;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .badge-red {
            color: #EF4444;
            background-color: rgba(239, 68, 68, 0.06);
            border: 1px solid rgba(239, 68, 68, 0.12);
        }
        .badge-green {
            color: #10B981;
            background-color: rgba(16, 185, 129, 0.06);
            border: 1px solid rgba(16, 185, 129, 0.12);
        }
        .trend-metric-block {
            display: flex;
            align-items: baseline;
            gap: 0.5rem;
            margin-top: 0.25rem;
        }
        /* Trends Card Target styling using :has() selector - FORCES EQUAL HEIGHT AND FLEX DISTRIBUTION */
        div[data-testid="stVerticalBlockBorderContainer"]:has(.trends-card-marker) {
            background-color: var(--card-bg) !important;
            background: var(--card-bg) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 20px !important;
            padding: 32px !important;
            box-shadow: 0 10px 40px rgba(15, 23, 42, 0.08) !important;
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            min-height: 505px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
        }
        .trend-metric-change {
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
        }
        .red-change {
            color: #EF4444;
        }
        .green-change {
            color: #64748B;
        }
        .trend-metric-lbl {
            font-size: 0.8rem;
            font-weight: 500;
            color: #64748B;
        }
        .trend-insight-box-new {
            border-radius: 10px;
            padding: 10px 12px;
            border: 1px solid var(--border-color);
            background-color: var(--bg-color);
            margin-top: auto;
        }
        .trend-insight-text-new {
            font-size: 0.76rem;
            margin: 0;
            line-height: 1.4;
            color: var(--text-color);
            opacity: 0.95;
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------------------------
    # Data pipeline
    # ---------------------------------------------------------------------------
    data = _cached_procurement_data()
    delivery_risk = _cached_delivery_risk()
    vendor_risk = _cached_vendor_risk()
    counts = alert_counts(delivery_risk=delivery_risk, vendor_risk=vendor_risk)

    health = _procurement_health_score(delivery_risk, vendor_risk, counts)
    total_active_pos = int(data["actual_delivery_date"].isna().sum())
    high_risk_deliveries = (
        int((delivery_risk["risk_level"] == "High").sum())
        if not delivery_risk.empty
        else 0
    )
    vendors_requiring_escalation = int((vendor_risk["risk_level"] == "High").sum())
    estimated_schedule_impact = (
        round(delivery_risk["expected_delay_days"].sum(), 1)
        if not delivery_risk.empty
        else 0
    )

    critical_material_count = 0
    if "criticality" in data.columns:
        critical_material_count = int((data["criticality"] == "Critical").sum())
    elif "priority" in data.columns:
        critical_material_count = int((data["priority"] == "Critical").sum())

    # ---------------------------------------------------------------------------
    # SECTION 1: Page Title & Subtitle (No Calendar Icon/Badge)
    # ---------------------------------------------------------------------------
    st.markdown(
        """
        <div class="overview-title-container">
            <div>
                <h1 class="overview-title">SiteSage AI Overview</h1>
                <p class="overview-subtitle">Real-time procurement intelligence and risk monitoring</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------------------------
    # SECTION 2: Executive Summary Card (Full Width - Emojis/Stars Removed)
    # ---------------------------------------------------------------------------
    st.markdown(
        f"""
        <div class="exec-summary-card">
            <div class="exec-content">
                <div class="exec-title">Executive Procurement Intelligence</div>
                <p class="exec-text">
                    Portfolio health is operating at <b>{health}%</b>. SiteSage AI has flagged <b>{high_risk_deliveries} active deliveries at high risk</b> representing potential schedule disruptions. There are <b>{vendors_requiring_escalation} vendors</b> requiring immediate strategic escalation. Float consumption across active project phases has reached a critical threshold, leading to <b>{estimated_schedule_impact} days of estimated cumulative schedule delay</b> across <b>{critical_material_count} critical materials</b>. Immediate manager action is recommended on the critical path items.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------------------------
    # SECTION 3: Single Row KPI Cards (Equal Sizes, Standardized Single-Line Captions)
    # ---------------------------------------------------------------------------
    col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5, col_kpi6 = st.columns(6)

    col_kpi1.markdown(
        f"""
        <div class="kpi-card-custom">
            <div class="kpi-card-header">
                <div class="kpi-icon-box" style="background-color: rgba(16, 185, 129, 0.1); color: #10B981;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                </div>
                <div class="kpi-label-box">
                    <span class="kpi-lbl">Health Score</span>
                    <span class="kpi-val">{health}%</span>
                </div>
            </div>
            <p class="kpi-cap">Portfolio Health</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_kpi2.markdown(
        f"""
        <div class="kpi-card-custom">
            <div class="kpi-card-header">
                <div class="kpi-icon-box" style="background-color: rgba(59, 130, 246, 0.1); color: #3B82F6;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                </div>
                <div class="kpi-label-box">
                    <span class="kpi-lbl">Active POs</span>
                    <span class="kpi-val">{total_active_pos}</span>
                </div>
            </div>
            <p class="kpi-cap">Total Active</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_kpi3.markdown(
        f"""
        <div class="kpi-card-custom">
            <div class="kpi-card-header">
                <div class="kpi-icon-box" style="background-color: rgba(239, 68, 68, 0.1); color: #EF4444;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                </div>
                <div class="kpi-label-box">
                    <span class="kpi-lbl">At-Risk POs</span>
                    <span class="kpi-val">{high_risk_deliveries}</span>
                </div>
            </div>
            <p class="kpi-cap">High Risk</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_kpi4.markdown(
        f"""
        <div class="kpi-card-custom">
            <div class="kpi-card-header">
                <div class="kpi-icon-box" style="background-color: rgba(245, 158, 11, 0.1); color: #F59E0B;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                </div>
                <div class="kpi-label-box">
                    <span class="kpi-lbl">Escalations</span>
                    <span class="kpi-val">{vendors_requiring_escalation}</span>
                </div>
            </div>
            <p class="kpi-cap">Active Vendors</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_kpi5.markdown(
        f"""
        <div class="kpi-card-custom">
            <div class="kpi-card-header">
                <div class="kpi-icon-box" style="background-color: rgba(139, 92, 246, 0.1); color: #8B5CF6;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                </div>
                <div class="kpi-label-box">
                    <span class="kpi-lbl">Delay Days</span>
                    <span class="kpi-val">{estimated_schedule_impact}d</span>
                </div>
            </div>
            <p class="kpi-cap">Estimated Delay</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_kpi6.markdown(
        f"""
        <div class="kpi-card-custom">
            <div class="kpi-card-header">
                <div class="kpi-icon-box" style="background-color: rgba(239, 68, 68, 0.1); color: #EF4444;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="16.5" y1="9.4" x2="7.5" y2="4.21"/><polygon points="12 22.08 12 12 3 6.92 3 17.08 12 22.08"/><polygon points="12 12 21 6.92 21 17.08 12 22.08"/><polygon points="12 2 21 6.92 12 12 3 6.92 12 2"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
                </div>
                <div class="kpi-label-box">
                    <span class="kpi-lbl">Critical Mat.</span>
                    <span class="kpi-val">{critical_material_count}</span>
                </div>
            </div>
            <p class="kpi-cap">Critical Materials</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------------------------
    # SECTION 4: AI Recommended Actions
    # ---------------------------------------------------------------------------
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="ai-actions-container">
                <div class="ai-actions-header">
                    <div class="ai-actions-header-left">
                        <div class="ai-logo-box">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m0-12.728l.707.707m11.314 11.314l.707-.707M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z"/>
                            </svg>
                        </div>
                        <div class="ai-actions-titles">
                            <span class="ai-actions-title">AI Recommended Actions</span>
                            <span class="ai-actions-subtitle">Prioritized actions based on risk impact and urgency</span>
                        </div>
                    </div>
                    <a href="?page=Alerts" target="_self" class="ai-actions-view-all">
                        <span>View all recommendations</span>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
                    </a>
                </div>
                <div class="ai-actions-grid">
                    <!-- Card 1 -->
                    <div class="ai-action-card">
                        <div class="ai-card-top">
                            <div class="ai-card-num-box">
                                <span class="ai-card-num">1</span>
                            </div>
                            <div class="ai-card-icon-wrapper">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                            </div>
                            <div class="ai-card-details">
                                <h5 class="ai-card-title">Escalate Keystone Bearing Systems</h5>
                                <p class="ai-card-desc">Formwork package is at 100% delay risk and impacting critical path.</p>
                            </div>
                        </div>
                        <div class="ai-card-bottom">
                            <span class="badge-priority-high">High Priority</span>
                            <span class="ai-card-due">Due Today</span>
                        </div>
                    </div>
                    <!-- Card 2 -->
                    <div class="ai-action-card">
                        <div class="ai-card-top">
                            <div class="ai-card-num-box">
                                <span class="ai-card-num">2</span>
                            </div>
                            <div class="ai-card-icon-wrapper">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                            </div>
                            <div class="ai-card-details">
                                <h5 class="ai-card-title">Review Cement Procurement</h5>
                                <p class="ai-card-desc">{vendors_requiring_escalation} vendors are exceeding lead-time threshold across multiple POs.</p>
                            </div>
                        </div>
                        <div class="ai-card-bottom">
                            <span class="badge-priority-high">High Priority</span>
                            <span class="ai-card-due">Due in 1 day</span>
                        </div>
                    </div>
                    <!-- Card 3 -->
                    <div class="ai-action-card">
                        <div class="ai-card-top">
                            <div class="ai-card-num-box">
                                <span class="ai-card-num">3</span>
                            </div>
                            <div class="ai-card-icon-wrapper-amber">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
                            </div>
                            <div class="ai-card-details">
                                <h5 class="ai-card-title">Validate Critical Path Dependencies</h5>
                                <p class="ai-card-desc">{critical_material_count} critical materials may impact project timeline if delayed.</p>
                            </div>
                        </div>
                        <div class="ai-card-bottom">
                            <span class="badge-priority-medium">Medium Priority</span>
                            <span class="ai-card-due">Due in 2 days</span>
                        </div>
                    </div>
                    <!-- Card 4 -->
                    <div class="ai-action-card">
                        <div class="ai-card-top">
                            <div class="ai-card-num-box">
                                <span class="ai-card-num">4</span>
                            </div>
                            <div class="ai-card-icon-wrapper-blue">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#4F8CFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
                            </div>
                            <div class="ai-card-details">
                                <h5 class="ai-card-title">Schedule Mitigation Planning</h5>
                                <p class="ai-card-desc">Estimated cumulative delay is {estimated_schedule_impact} days. Mitigation plan recommended.</p>
                            </div>
                        </div>
                        <div class="ai-card-bottom">
                            <span class="badge-priority-medium">Medium Priority</span>
                            <span class="ai-card-due">Due in 3 days</span>
                        </div>
                    </div>
                </div>
                <div class="ai-actions-footer">
                    <div class="ai-actions-footer-left">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--primary-blue);"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                        <span>These actions are AI-generated based on risk severity, schedule impact, and procurement criticality.</span>
                    </div>
                    <div class="ai-actions-footer-right">
                        <span>Last updated: Just now</span>
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---------------------------------------------------------------------------
    # SECTION 5: Two-Column Layout
    # ---------------------------------------------------------------------------
    col_left, col_right = st.columns([7, 3])

    with col_left:
        with st.container(border=True):
            st.html(
                """
                <div class="col-card-header">
                    <span class="col-card-title">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--critical)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                        <span>Top At-Risk Materials</span>
                    </span>
                    <a href="?page=Alerts" target="_self" class="col-card-link">View all</a>
                </div>
                """
            )

            high_risk_table = delivery_risk.sort_values(
                by="risk_score", ascending=False
            ).head(5)
            if not high_risk_table.empty:
                table_rows = ""
                for _, row in high_risk_table.iterrows():
                    risk_score = int(row["risk_score"])
                    impact = get_impact_status(row)

                    # Progress fill color using variables
                    if risk_score >= 70:
                        fill_color = "var(--critical)"
                    elif risk_score >= 40:
                        fill_color = "var(--warning)"
                    else:
                        fill_color = "var(--success)"

                    table_rows += f"""
                    <tr>
                       <td>
                          <div class="mat-cell">
                             <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--text-color)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="opacity: 0.6; margin-right: 0.1rem;"><path d="M12.89 2.24l9 4.39a2 2 0 0 1 1 1.72v8.6a2 2 0 0 1-1 1.72l-9 4.39a2 2 0 0 1-1.78 0l-9-4.39a2 2 0 0 1-1-1.72V8.35a2 2 0 0 1 1-1.72l9-4.39a2 2 0 0 1 1.78 0z"/></svg>
                             <span>{row['material_name']}</span>
                          </div>
                       </td>
                       <td><div class="vendor-cell">{row['vendor_name']}</div></td>
                       <td><span class="badge-sev badge-sev-{row['risk_level']}">{row['risk_level']}</span></td>
                       <td>
                          <div class="prog-container">
                             <span style="font-weight:600; min-width:32px; font-size: 0.8rem; color: var(--text-color);">{risk_score}%</span>
                             <div class="prog-bar">
                                <div class="prog-fill" style="width: {risk_score}%; background-color: {fill_color};"></div>
                             </div>
                          </div>
                       </td>
                       <td><b>{int(row['expected_delay_days'])}</b></td>
                       <td><span class="badge-sev badge-sev-{impact}">{impact}</span></td>
                    </tr>
                    """

                table_html = f"""
                <table class="custom-table">
                    <thead>
                        <tr>
                            <th>Material</th>
                            <th>Vendor</th>
                            <th>Risk Level</th>
                            <th>Delay Risk</th>
                            <th>Est. Delay (Days)</th>
                            <th>Impact</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
                """
                render_clean_html(table_html)
            else:
                st.info("No high-risk procurement issues detected.")

    with col_right:
        with st.container(border=True):
            st.html(
                """
                <div class="col-card-header">
                    <span class="col-card-title">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--critical)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
                        <span>Critical Alerts</span>
                    </span>
                    <a href="?page=Alerts" target="_self" class="col-card-link">View all</a>
                </div>
                """
            )

            alerts = generate_alerts(delivery_risk=delivery_risk, vendor_risk=vendor_risk)
            delivery_alerts = [a for a in alerts if a.get("type") == "Delivery Risk"]
            critical_alerts = [
                a for a in delivery_alerts if a["severity"] in ["Critical", "High"]
            ][:3]

            if critical_alerts:
                alert_items_html = ""
                for alert in critical_alerts:
                    detail = alert["detail"]
                    title = alert["title"]
                    severity = alert["severity"]

                    po = "PO-XXXX"
                    vendor = "Unknown Vendor"
                    expected_roj = "N/A"
                    delay_risk = "0"

                    import re
                    match = re.match(r"^([^\s]+) from (.+?) has (\d+)% delay risk and expected ROJ (.+?)\.?$", detail)
                    if match:
                        po, vendor, delay_risk, expected_roj = match.groups()

                    alert_items_html += f"""
                    <div class="alert-row-item alert-border-{severity}">
                       <div class="alert-item-header">
                          <span class="alert-item-meta">{po} • {vendor}</span>
                          <span class="badge-sev badge-sev-{severity}">{severity}</span>
                       </div>
                       <div class="alert-item-title">{title}</div>
                       <div class="alert-item-dates">
                          <span>Expected ROJ: <b>{expected_roj}</b></span>
                          <span>Delay Risk: <b>{delay_risk}%</b></span>
                       </div>
                    </div>
                    """

                alert_container_html = f"""
                <div class="alert-list-container">
                    {alert_items_html}
                </div>
                """
                render_clean_html(alert_container_html)
            else:
                st.info("No active critical alerts detected.")

    # ---------------------------------------------------------------------------
    # SECTION 6: Bottom Charts
    # ---------------------------------------------------------------------------
    df_proc = load_procurement_data()
    df_proc["order_date_dt"] = pd.to_datetime(df_proc["order_date"], errors="coerce")
    df_proc["month"] = df_proc["order_date_dt"].dt.to_period("M").astype(str)
    monthly_summary = (
        df_proc.groupby("month")
        .agg(
            total_orders=("po_number", "count"),
            total_spend=("contract_value", "sum"),
            avg_delay=("observed_delay_days", "mean"),
        )
        .reset_index()
        .sort_values("month")
    )
    monthly_summary = monthly_summary[monthly_summary["month"] != "NaT"]

    # Create schedule impact summary
    summary = schedule_impact_summary(data)
    impact_df = pd.DataFrame(
        [
            {
                "Status": "Critical Path Blocked",
                "Count": summary["critical_path_blocked"],
                "Color": "#EF4444",
            },
            {
                "Status": "Float Consumed",
                "Count": summary["float_consumed"],
                "Color": "#F59E0B",
            },
            {
                "Status": "On Track",
                "Count": summary["on_track"],
                "Color": "#10B981",
            },
        ]
    )

    is_dark = st.session_state.get("theme", "light") == "dark"
    grid_color = "#2D3748" if is_dark else "#F1F5F9"
    chart_font_color = "#94A3B8" if is_dark else "#64748B"
    plotly_template = "plotly_dark" if is_dark else "plotly_white"

    # Map months to clean labels (e.g., 2026-03 -> Mar)
    month_map = {
        "2026-01": "Jan", "2026-02": "Feb", "2026-03": "Mar", 
        "2026-04": "Apr", "2026-05": "May", "2026-06": "Jun",
        "2026-07": "Jul", "2026-08": "Aug", "2026-09": "Sep",
        "2026-10": "Oct", "2026-11": "Nov", "2026-12": "Dec"
    }
    monthly_summary["month_label"] = monthly_summary["month"].map(lambda x: month_map.get(x, x))

    # Section Header: Procurement Trends
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 2rem; margin-bottom: 1.25rem;">
            <div style="display: flex; flex-direction: column; gap: 0.25rem;">
                <h3 style="font-size: 1.15rem; font-weight: 700; color: var(--primary-navy); margin: 0;">Procurement Trends</h3>
                <p style="font-size: 0.82rem; color: var(--text-color); opacity: 0.7; margin: 0;">Track procurement risk, schedule impact, and delivery performance over time.</p>
            </div>
            <a href="?page=Procurement" target="_self" style="font-size: 0.8rem; font-weight: 600; color: var(--primary-blue); text-decoration: none; display: flex; align-items: center; gap: 0.25rem; transition: opacity 0.2s ease;">
                <span>View Full Analytics</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        with st.container(border=True):
            st.markdown(
                """
                <div class="trends-card-marker"></div>
                <div class="trend-card-header-new">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; width: 100%;">
                        <div>
                            <h4 class="trend-title-new">Vendor Risk Trend</h4>
                            <p class="trend-subtitle-new">Average delivery delay over time</p>
                        </div>
                        <span class="trend-badge-new badge-red">HIGH RISK</span>
                    </div>
                    <div class="trend-metric-block">
                        <span class="trend-metric-val">6.2 Days</span>
                        <span class="trend-metric-change red-change" style="margin-left: 0.5rem;">↑ 18% Risk Increase</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            fig_vendor_trend = px.line(
                monthly_summary,
                x="month_label",
                y="avg_delay",
                template=plotly_template,
            )
            fig_vendor_trend.update_traces(
                fill='tozeroy',
                fillcolor='rgba(239, 68, 68, 0.12)',
                line=dict(color="#EF4444", width=3, shape='spline'),
                mode='lines'
            )
            fig_vendor_trend.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                height=220,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    showgrid=False, 
                    title="", 
                    visible=True,
                    showline=False,
                    tickfont=dict(size=10, color="#94A3B8")
                ),
                yaxis=dict(
                    showgrid=False, 
                    visible=False
                ),
            )
            st.plotly_chart(fig_vendor_trend, use_container_width=True, theme=None, config={'displayModeBar': False})
            st.markdown(
                """
                <div class="trend-insight-box-new">
                    <p class="trend-insight-text-new">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2.5" style="flex-shrink: 0;"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                        <span><b>Vendor delays are accelerating.</b> Escalation recommended.</span>
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with c2:
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="trends-card-marker"></div>
                <div class="trend-card-header-new">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; width: 100%;">
                        <div>
                            <h4 class="trend-title-new">Schedule Impact Breakdown</h4>
                            <p class="trend-subtitle-new">Deliveries impacting project timeline</p>
                        </div>
                    </div>
                    <div class="trend-metric-block">
                        <span class="trend-metric-val">{high_risk_deliveries}</span>
                        <span class="trend-metric-lbl" style="margin-left: 0.5rem; font-weight: 500; color: #64748B;">Impacted Deliveries</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            fig_schedule = px.bar(
                impact_df,
                x="Status",
                y="Count",
                color="Status",
                text="Count",
                color_discrete_map={
                    "Critical Path Blocked": "#EF4444",
                    "Float Consumed": "#F59E0B",
                    "On Track": "#10B981",
                },
                template=plotly_template,
            )
            fig_schedule.update_traces(
                textposition="outside",
                textfont=dict(size=11, family="Plus Jakarta Sans", color=chart_font_color, weight="bold"),
                width=0.4,
                cliponaxis=False
            )
            fig_schedule.update_layout(
                margin=dict(l=10, r=10, t=25, b=10),
                height=220,
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    showgrid=False, 
                    title="", 
                    showline=False,
                    tickfont=dict(size=10, color="#94A3B8")
                ),
                yaxis=dict(
                    showgrid=False, 
                    visible=False
                ),
                barcornerradius=8,
            )
            st.plotly_chart(fig_schedule, use_container_width=True, theme=None, config={'displayModeBar': False})
            st.markdown(
                """
                <div class="trend-insight-box-new">
                    <p class="trend-insight-text-new">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2.5" style="flex-shrink: 0;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg>
                        <span><b>318 materials</b> are blocking critical path activities.</span>
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with c3:
        with st.container(border=True):
            st.markdown(
                """
                <div class="trends-card-marker"></div>
                <div class="trend-card-header-new">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; width: 100%;">
                        <div>
                            <h4 class="trend-title-new">Procurement Performance Trend</h4>
                            <p class="trend-subtitle-new">On-time delivery performance</p>
                        </div>
                        <span class="trend-badge-new badge-green">ON TRACK</span>
                    </div>
                    <div class="trend-metric-block">
                        <span class="trend-metric-val">68%</span>
                        <span class="trend-metric-lbl-green" style="color: #10B981; font-weight: 600; font-size: 0.82rem; margin-left: 0.5rem; display: inline-flex; align-items: center; gap: 0.25rem;">
                            <span style="width: 7px; height: 7px; background-color: #10B981; border-radius: 50%; display: inline-block;"></span>
                            On-Time Performance
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            fig_perf_trend = px.line(
                monthly_summary,
                x="month_label",
                y="total_orders",
                template=plotly_template,
            )
            fig_perf_trend.update_traces(
                fill='tozeroy',
                fillcolor='rgba(79, 140, 255, 0.08)',
                line=dict(color="#4F8CFF", width=3, shape='spline'),
                mode='lines'
            )
            fig_perf_trend.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                height=220,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    showgrid=False, 
                    title="", 
                    visible=True,
                    showline=False,
                    tickfont=dict(size=10, color="#94A3B8")
                ),
                yaxis=dict(
                    showgrid=False, 
                    visible=False
                ),
            )
            st.plotly_chart(fig_perf_trend, use_container_width=True, theme=None, config={'displayModeBar': False})
            st.markdown(
                """
                <div class="trend-insight-box-new">
                    <p class="trend-insight-text-new">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5" style="flex-shrink: 0;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                        <span><b>Slight decline in performance.</b> Monitor closely.</span>
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
