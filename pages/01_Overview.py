import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.alerts import alert_counts, generate_alerts
from src.database import count_rows
from src.delay_model import get_delivery_risk_table, load_procurement_data
from src.schedule_impact import get_schedule_impact_table, schedule_impact_summary
from src.vendor_risk import get_vendor_risk_table


# ---------------------------------------------------------------------------
# Custom CSS for Command Center cards
# ---------------------------------------------------------------------------
COMMAND_CENTER_CSS = """
<style>
.cc-card {
    background: white;
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    margin: 0.4rem 0;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.cc-card-danger {
    border-left: 4px solid #b91c1c;
}
.cc-card-warn {
    border-left: 4px solid #b45309;
}
.cc-card-ok {
    border-left: 4px solid #0f766e;
}
.cc-title {
    font-size: 0.82rem;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.3rem;
}
.cc-value {
    font-size: 1.8rem;
    font-weight: 700;
    line-height: 1.1;
}
.cc-value-danger { color: #b91c1c; }
.cc-value-warn { color: #b45309; }
.cc-value-ok { color: #0f766e; }
.cc-subtitle {
    font-size: 0.78rem;
    color: #94a3b8;
    margin-top: 0.2rem;
}
.cc-banner {
    background: linear-gradient(135deg, #0f766e08, #0f766e15);
    border: 1px solid #0f766e30;
    border-radius: 14px;
    padding: 1.3rem 1.8rem;
    margin-bottom: 1.2rem;
}
.cc-banner-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #0f766e;
    margin: 0 0 0.2rem 0;
}
.cc-banner-sub {
    font-size: 0.85rem;
    color: #64748b;
}
.cc-item {
    background: #f8fafc;
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin: 0.3rem 0;
    border: 1px solid #e2e8f0;
}
.cc-item-title {
    font-weight: 600;
    font-size: 0.88rem;
    color: #1e293b;
}
.cc-item-detail {
    font-size: 0.8rem;
    color: #64748b;
    margin-top: 0.15rem;
}
.cc-badge {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    margin-left: 0.5rem;
}
.cc-badge-high { background: #b91c1c18; color: #b91c1c; }
.cc-badge-med { background: #b4530918; color: #b45309; }
.cc-badge-low { background: #0f766e18; color: #0f766e; }
</style>
"""


def _procurement_health_score(delivery_risk, vendor_risk, counts):
    """Compute an overall procurement health score (0-100)."""
    if delivery_risk.empty:
        return 85  # Default healthy

    high_risk_items = (delivery_risk["risk_level"] == "High").sum()
    total_items = len(delivery_risk)
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
    st.title("SiteSage AI Overview")
    st.markdown(COMMAND_CENTER_CSS, unsafe_allow_html=True)

    data = load_procurement_data()
    delivery_risk = get_delivery_risk_table()
    vendor_risk = get_vendor_risk_table(data)
    counts = alert_counts()

    # ===================================================================
    # PROCUREMENT COMMAND CENTER
    # ===================================================================
    st.markdown(
        """
        <div class="cc-banner">
            <div class="cc-banner-title">🎯 Procurement Command Center</div>
            <div class="cc-banner-sub">
                Real-time procurement intelligence • At-risk items • Vendor escalation • Schedule impact
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Top KPI Row ---
    health = _procurement_health_score(delivery_risk, vendor_risk, counts)
    at_risk_count = int((delivery_risk["risk_level"] == "High").sum()) if not delivery_risk.empty else 0
    escalation_count = int((vendor_risk["risk_level"] == "High").sum())
    total_impact_days = round(delivery_risk["expected_delay_days"].sum(), 1) if not delivery_risk.empty else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Indexed Documents", count_rows("documents"))
    k2.metric("Open Purchase Orders", int(data["actual_delivery_date"].isna().sum()))
    k3.metric("🔴 At-Risk Items", at_risk_count)
    k4.metric("⚠️ Vendor Escalations", escalation_count)
    k5.metric("📅 Impact Days (Total)", total_impact_days)

    # --- Three-panel Command Center ---
    panel1, panel2, panel3 = st.columns(3)

    # Panel 1: At-Risk Items
    with panel1:
        st.markdown(
            '<div class="cc-title">🔴 At-Risk Items</div>',
            unsafe_allow_html=True,
        )
        if not delivery_risk.empty:
            high_risk = delivery_risk[delivery_risk["risk_level"] == "High"].head(5)
            if high_risk.empty:
                st.markdown(
                    '<div class="cc-card cc-card-ok"><span class="cc-value cc-value-ok">✓</span>'
                    '<div class="cc-subtitle">No high-risk items</div></div>',
                    unsafe_allow_html=True,
                )
            else:
                for _, row in high_risk.iterrows():
                    badge_class = "cc-badge-high"
                    st.markdown(
                        f"""
                        <div class="cc-item">
                            <div class="cc-item-title">
                                {row['material_name']}
                                <span class="cc-badge {badge_class}">{row['risk_score']}%</span>
                            </div>
                            <div class="cc-item-detail">
                                {row['vendor_name']} • {row['po_number']}<br>
                                Expected delay: <b>{row['expected_delay_days']} days</b>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.info("No delivery risk data available.")

    # Panel 2: Vendors Needing Escalation
    with panel2:
        st.markdown(
            '<div class="cc-title">⚠️ Vendors Needing Escalation</div>',
            unsafe_allow_html=True,
        )
        high_vendors = vendor_risk[vendor_risk["risk_level"] == "High"].head(5)
        if high_vendors.empty:
            st.markdown(
                '<div class="cc-card cc-card-ok"><span class="cc-value cc-value-ok">✓</span>'
                '<div class="cc-subtitle">All vendors within tolerance</div></div>',
                unsafe_allow_html=True,
            )
        else:
            for _, vrow in high_vendors.iterrows():
                st.markdown(
                    f"""
                    <div class="cc-item">
                        <div class="cc-item-title">
                            {vrow['vendor_name']}
                            <span class="cc-badge cc-badge-high">High Risk</span>
                        </div>
                        <div class="cc-item-detail">
                            On-time: {vrow['on_time_rate']}% • Avg delay: {vrow['avg_delay_days']}d<br>
                            Action: {vrow['recommendation'][:60]}…
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # Panel 3: Schedule Impact Summary
    with panel3:
        st.markdown(
            '<div class="cc-title">📅 Schedule Impact Summary</div>',
            unsafe_allow_html=True,
        )
        # Health gauge
        fig_gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=health,
                title={"text": "Procurement Health", "font": {"size": 14}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1},
                    "bar": {"color": "#0f766e" if health >= 60 else "#b45309" if health >= 35 else "#b91c1c"},
                    "steps": [
                        {"range": [0, 35], "color": "#b91c1c18"},
                        {"range": [35, 60], "color": "#b4530918"},
                        {"range": [60, 100], "color": "#0f766e18"},
                    ],
                    "threshold": {
                        "line": {"color": "#1e293b", "width": 2},
                        "thickness": 0.75,
                        "value": health,
                    },
                },
                number={"suffix": "%"},
            )
        )
        fig_gauge.update_layout(height=180, margin=dict(l=20, r=20, t=30, b=10))
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown(
            f"""
            <div class="cc-card cc-card-{'danger' if total_impact_days > 30 else 'warn' if total_impact_days > 10 else 'ok'}">
                <div class="cc-title">Estimated Total Impact</div>
                <div class="cc-value cc-value-{'danger' if total_impact_days > 30 else 'warn' if total_impact_days > 10 else 'ok'}">
                    {total_impact_days} days
                </div>
                <div class="cc-subtitle">Across {at_risk_count} at-risk items</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # ===================================================================
    # ORIGINAL OVERVIEW SECTIONS (enhanced)
    # ===================================================================
    left, right = st.columns([1.35, 1])
    with left:
        st.subheader("Delivery Risk Pipeline")
        if not delivery_risk.empty:
            chart_df = delivery_risk.head(8)
            fig = px.bar(
                chart_df,
                x="risk_score",
                y="material_name",
                color="risk_level",
                orientation="h",
                hover_data=["po_number", "vendor_name", "expected_roj_date"],
                color_discrete_map={"High": "#b91c1c", "Medium": "#b45309", "Low": "#0f766e"},
            )
            fig.update_layout(
                xaxis_title="Risk score",
                yaxis_title="",
                height=360,
                margin=dict(l=10, r=20, t=20, b=20),
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No delivery risk data.")

    with right:
        st.subheader("Top Alerts")
        for alert in generate_alerts()[:5]:
            st.markdown(
                f"**{alert['severity']} - {alert['title']}**  \n"
                f"{alert['detail']}  \n"
                f"Action: {alert['action']}"
            )

    st.subheader("Open Orders Requiring Attention")
    if not delivery_risk.empty:
        st.dataframe(
            delivery_risk[
                [
                    "po_number",
                    "material_name",
                    "vendor_name",
                    "promised_delivery_date",
                    "expected_roj_date",
                    "risk_level",
                    "risk_score",
                ]
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("No open orders.")

    st.divider()

    # ===================================================================
    # SCHEDULE IMPACT MAPPING
    # ===================================================================
    st.subheader("📊 Schedule Impact Mapping")
    st.caption(
        "Shows whether late materials consume schedule float or block the critical path."
    )

    impact_table = get_schedule_impact_table(data)
    summary = schedule_impact_summary(data)

    si1, si2, si3 = st.columns(3)
    si1.metric(
        "🔴 Critical Path Blocked",
        summary["critical_path_blocked"],
    )
    si2.metric(
        "🟡 Float Consumed",
        summary["float_consumed"],
    )
    si3.metric(
        "🟢 On Track",
        summary["on_track"],
    )

    if not impact_table.empty:
        # Color-coded display
        st.dataframe(
            impact_table[
                [
                    "material_name",
                    "vendor_name",
                    "po_number",
                    "project_phase",
                    "delay_days",
                    "phase_float",
                    "float_remaining",
                    "impact_status",
                ]
            ].rename(
                columns={
                    "material_name": "Material",
                    "vendor_name": "Vendor",
                    "po_number": "PO #",
                    "project_phase": "Phase",
                    "delay_days": "Delay (days)",
                    "phase_float": "Phase Float",
                    "float_remaining": "Float Left",
                    "impact_status": "Impact Status",
                }
            ),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("No items with schedule impact detected.")
