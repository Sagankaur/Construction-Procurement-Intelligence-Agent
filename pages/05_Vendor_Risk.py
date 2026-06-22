import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from src.vendor_risk import (
    compare_vendors,
    get_vendor_details,
    get_vendor_risk_table,
)

# Premium UI CSS styling for Vendor 360
VENDOR_360_CSS = """
<style>
.vendor-card {
    background: white;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin: 0.5rem 0 1rem 0;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}
.vendor-title {
    font-size: 1.3rem;
    font-weight: 700;
    color: #0f766e;
    margin-bottom: 0.2rem;
}
.vendor-subtitle {
    font-size: 0.85rem;
    color: #64748b;
    margin-bottom: 1rem;
}
.vendor-badge {
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 12px;
    margin-bottom: 0.5rem;
}
.badge-high { background-color: #b91c1c18; color: #b91c1c; border: 1px solid #b91c1c30; }
.badge-med { background-color: #b4530918; color: #b45309; border: 1px solid #b4530930; }
.badge-low { background-color: #0f766e18; color: #0f766e; border: 1px solid #0f766e30; }

.recom-box {
    background-color: #f8fafc;
    border-left: 4px solid #0f766e;
    border-radius: 6px;
    padding: 0.8rem 1.2rem;
    font-size: 0.85rem;
    color: #334155;
    margin-top: 0.8rem;
}
.recom-box-high { border-left-color: #b91c1c; }
.recom-box-med { border-left-color: #b45309; }
</style>
"""


def render_overview_tab(table):
    st.subheader("Vendor Performance Directory")

    col1, col2, col3 = st.columns(3)
    col1.metric("Tracked Vendors", len(table))
    col2.metric("🔴 High Risk Vendors", int((table["risk_level"] == "High").sum()))
    col3.metric("Average On-Time Rate", f"{table['on_time_rate'].mean():.1f}%")

    st.markdown("---")

    # Risk Score Distribution Chart
    fig = px.bar(
        table,
        x="vendor_name",
        y="risk_score",
        color="risk_level",
        hover_data=["on_time_rate", "avg_delay_days", "materials"],
        color_discrete_map={"High": "#b91c1c", "Medium": "#b45309", "Low": "#0f766e"},
        labels={
            "vendor_name": "Vendor Name",
            "risk_score": "Risk Score (0-100)",
            "risk_level": "Risk Tier",
        },
    )
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Risk Score",
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(table, width="stretch", hide_index=True)


def render_drilldown_tab(table):
    st.subheader("Vendor 360° Profile & Drill-Down")

    selected_vendor = st.selectbox(
        "Select Vendor to Inspect",
        sorted(table["vendor_name"].unique()),
    )

    details = get_vendor_details(selected_vendor)
    if not details:
        st.error("No vendor details found.")
        return

    profile = details["profile"]
    badge_cls = (
        "badge-high"
        if profile["risk_level"] == "High"
        else "badge-med"
        if profile["risk_level"] == "Medium"
        else "badge-low"
    )
    recom_cls = (
        "recom-box-high"
        if profile["risk_level"] == "High"
        else "recom-box-med"
        if profile["risk_level"] == "Medium"
        else ""
    )

    st.markdown(
        f"""
        <div class="vendor-card">
            <span class="vendor-badge {badge_cls}">{profile['risk_level']} Risk Tier</span>
            <div class="vendor-title">{profile['vendor_name']}</div>
            <div class="vendor-subtitle">Procurement Spend Profile & Performance Metrics</div>
            <div class="recom-box {recom_cls}">
                <b>Strategic Recommendation:</b> {profile['recommendation']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Core Metrics Row
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Spend", f"${details['total_spend']:,.2f}")
    m2.metric("Total Orders", profile["orders"])
    m3.metric("Open Orders", profile["open_orders"])
    m4.metric("On-Time Rate", f"{profile['on_time_rate']}%")
    m5.metric("Avg Delay", f"{profile['avg_delay_days']} days")

    # Metrics Breakdown Columns
    left, right = st.columns([1, 1])

    with left:
        st.subheader("Order Status Distribution")
        status_df = pd.DataFrame(
            [{"Status": k.title(), "Count": v} for k, v in details["status_counts"].items()]
        )
        if not status_df.empty:
            fig_pie = px.pie(
                status_df,
                names="Status",
                values="Count",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig_pie.update_layout(
                height=260,
                margin=dict(l=10, r=10, t=10, b=10),
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No status data available.")

    with right:
        st.subheader("Capabilities & Supplied Materials")
        st.markdown(f"**Primary Categories:** {', '.join(details['categories']) or 'None'}")
        st.markdown("**Supplied Materials:**")
        for mat in details["materials"]:
            st.markdown(f"- {mat}")

    st.subheader("Monthly Spend & Order Trend")
    trend_data = details["monthly_trend"]
    if trend_data:
        trend_df = pd.DataFrame(trend_data)
        fig_trend = go.Figure()
        fig_trend.add_trace(
            go.Bar(
                x=trend_df["month"],
                y=trend_df["spend"],
                name="Spend ($)",
                yaxis="y",
                marker_color="#0f766e",
                opacity=0.85,
            )
        )
        fig_trend.add_trace(
            go.Scatter(
                x=trend_df["month"],
                y=trend_df["orders"],
                name="Orders Count",
                yaxis="y2",
                line=dict(color="#b45309", width=3),
                mode="lines+markers",
            )
        )
        fig_trend.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=20, b=10),
            yaxis=dict(title="Spend ($)", side="left"),
            yaxis2=dict(title="Orders Count", side="right", overlaying="y"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No trend data available.")

    st.subheader("Purchase Order Records")
    records_df = pd.DataFrame(details["order_records"])
    if not records_df.empty:
        st.dataframe(
            records_df[
                [
                    "po_number",
                    "material_name",
                    "order_date",
                    "promised_delivery_date",
                    "actual_delivery_date",
                    "contract_value",
                    "current_status",
                ]
            ].rename(
                columns={
                    "po_number": "PO #",
                    "material_name": "Material",
                    "order_date": "Ordered",
                    "promised_delivery_date": "Promised",
                    "actual_delivery_date": "Actual",
                    "contract_value": "Value ($)",
                    "current_status": "Status",
                }
            ),
            width="stretch",
            hide_index=True,
        )


def render_comparison_tab(table):
    st.subheader("Side-by-Side Vendor Comparison")

    vendors_to_compare = st.multiselect(
        "Select Vendors to Compare",
        sorted(table["vendor_name"].unique()),
        default=sorted(table["vendor_name"].unique())[:2],
    )

    if not vendors_to_compare:
        st.warning("Please select at least one vendor to compare.")
        return

    comp_df = compare_vendors(vendors_to_compare)

    # 1. Comparative Metrics Bar Chart
    st.subheader("Risk Score Comparison")
    fig_comp = px.bar(
        comp_df,
        x="vendor_name",
        y="risk_score",
        color="risk_level",
        hover_data=["on_time_rate", "avg_delay_days"],
        color_discrete_map={"High": "#b91c1c", "Medium": "#b45309", "Low": "#0f766e"},
        labels={"vendor_name": "Vendor", "risk_score": "Risk Score"},
    )
    fig_comp.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_comp, use_container_width=True)

    # 2. Side-by-side Table
    st.subheader("Key Statistics Breakdown")
    st.dataframe(
        comp_df[
            [
                "vendor_name",
                "risk_level",
                "risk_score",
                "orders",
                "open_orders",
                "on_time_rate",
                "avg_delay_days",
                "quality_issues",
                "communication_score",
            ]
        ].rename(
            columns={
                "vendor_name": "Vendor",
                "risk_level": "Risk Tier",
                "risk_score": "Risk Score",
                "orders": "Orders",
                "open_orders": "Open",
                "on_time_rate": "On-Time %",
                "avg_delay_days": "Avg Delay (d)",
                "quality_issues": "Quality Issues",
                "communication_score": "Communication",
            }
        ),
        width="stretch",
        hide_index=True,
    )


def main():
    st.title("Vendor 360 View")
    st.markdown(VENDOR_360_CSS, unsafe_allow_html=True)

    table = get_vendor_risk_table()

    t1, t2, t3 = st.tabs(
        [
            "📊 Vendor Performance Overview",
            "🔍 Vendor 360 Drill-Down",
            "⚖️ Compare Vendors",
        ]
    )

    with t1:
        render_overview_tab(table)
    with t2:
        render_drilldown_tab(table)
    with t3:
        render_comparison_tab(table)


if __name__ == "__main__":
    main()
