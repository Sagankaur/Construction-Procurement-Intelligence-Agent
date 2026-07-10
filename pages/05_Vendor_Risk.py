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
.vendor-banner {
    background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
    border: 1px solid #FFCC80;
    border-radius: 14px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 12px rgba(255, 152, 0, 0.05);
}
.vendor-banner-title {
    font-size: 1.3rem;
    font-weight: 800;
    margin-bottom: 0.3rem;
    color: #07315F !important;
}
.vendor-banner-sub {
    font-size: 0.88rem;
    color: #4A5568 !important;
}

.vendor-card {
    background: var(--card-bg);
    border-radius: 12px;
    padding: 1.5rem;
    margin: 0.5rem 0 1.2rem 0;
    border: 1px solid var(--border-color);
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}
.vendor-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: var(--text-color);
    margin-bottom: 0.25rem;
}
.vendor-subtitle {
    font-size: 0.82rem;
    color: var(--text-color);
    opacity: 0.8;
    margin-bottom: 1rem;
}
.vendor-badge {
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 8px;
    margin-bottom: 0.6rem;
    text-transform: uppercase;
}
.badge-high { background-color: rgba(239, 68, 68, 0.08); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.2); }
.badge-med { background-color: rgba(245, 158, 11, 0.08); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.2); }
.badge-low { background-color: rgba(16, 185, 129, 0.08); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.2); }

.recom-box {
    background-color: var(--bg-color);
    border-left: 4px solid #3B82F6;
    border-radius: 8px;
    padding: 1rem 1.3rem;
    font-size: 0.88rem;
    color: var(--text-color);
    margin-top: 1rem;
    line-height: 1.5;
    border: 1px solid var(--border-color);
}
.recom-box-high { border-left-color: #EF4444; background-color: rgba(239, 68, 68, 0.12); }
.recom-box-med { border-left-color: #F59E0B; background-color: rgba(245, 158, 11, 0.12); }
</style>
"""


def render_overview_tab(table):
    st.markdown("<h3 style='margin-top:0.5rem;'>Vendor Performance Directory</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Tracked Vendors", len(table))
    col2.metric("🔴 High Risk Vendors", int((table["risk_level"] == "High").sum()))
    col3.metric("Average On-Time Rate", f"{table['on_time_rate'].mean():.1f}%")

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    is_dark = st.session_state.get("theme", "light") == "dark"
    grid_color = "#334155" if is_dark else "#E2E8F0"
    chart_font_color = "#94A3B8" if is_dark else "#475569"
    plotly_template = "plotly_dark" if is_dark else "plotly_white"

    # Risk Score Distribution Chart
    fig = px.bar(
        table,
        x="vendor_name",
        y="risk_score",
        color="risk_level",
        hover_data=["on_time_rate", "avg_delay_days", "materials"],
        color_discrete_map={"High": "#EF4444", "Medium": "#F59E0B", "Low": "#10B981"},
        labels={
            "vendor_name": "Vendor Name",
            "risk_score": "Risk Score (0-100)",
            "risk_level": "Risk Tier",
        },
        title="Vendor Risk Score Profile (0-100)",
        template=plotly_template,
    )
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Risk Score",
        height=320,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=grid_color),
        font=dict(family="Plus Jakarta Sans", size=11, color=chart_font_color),
    )
    st.plotly_chart(fig, use_container_width=True, theme=None)

    st.dataframe(
        table.rename(
            columns={
                "vendor_name": "Vendor Name",
                "risk_level": "Risk Level",
                "risk_score": "Risk Score",
                "orders": "Total Orders",
                "open_orders": "Open POs",
                "on_time_rate": "On-Time Rate (%)",
                "avg_delay_days": "Avg Delay (Days)",
                "materials": "Materials Supplied"
            }
        ),
        column_config={
            "Risk Score": st.column_config.ProgressColumn("Risk Score", min_value=0, max_value=100, format="%d%%"),
        },
        width="stretch",
        hide_index=True,
        use_container_width=True
    )


def render_drilldown_tab(table):
    st.markdown("<h3 style='margin-top:0.5rem;'>Vendor 360° Profile & Drill-Down</h3>", unsafe_allow_html=True)

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
        f"""<div class="vendor-card">
<span class="vendor-badge {badge_cls}">{profile['risk_level']} Risk Tier</span>
<div class="vendor-title">{profile['vendor_name']}</div>
<div class="vendor-subtitle">Procurement Spend Profile & Performance Metrics</div>
<div class="recom-box {recom_cls}">
<b>Strategic Recommendation:</b> {profile['recommendation']}
</div>
</div>""",
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
        st.markdown("<h4 style='margin-top:1.5rem;'>Order Status Distribution</h4>", unsafe_allow_html=True)
        status_df = pd.DataFrame(
            [{"Status": k.title(), "Count": v} for k, v in details["status_counts"].items()]
        )
        if not status_df.empty:
            is_dark = st.session_state.get("theme", "light") == "dark"
            chart_font_color = "#94A3B8" if is_dark else "#475569"
            plotly_template = "plotly_dark" if is_dark else "plotly_white"

            fig_pie = px.pie(
                status_df,
                names="Status",
                values="Count",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Safe,
                template=plotly_template,
            )
            fig_pie.update_layout(
                height=240,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans", size=11, color=chart_font_color),
            )
            st.plotly_chart(fig_pie, use_container_width=True, theme=None)
        else:
            st.info("No status data available.")

    with right:
        st.markdown("<h4 style='margin-top:1.5rem;'>Capabilities & Supplied Materials</h4>", unsafe_allow_html=True)
        st.markdown(f"**Primary Categories:** {', '.join(details['categories']) or 'None'}")
        st.markdown("**Supplied Materials:**")
        for mat in details["materials"]:
            st.markdown(f"- {mat}")

    st.markdown("<h4>Monthly Spend & Order Trend</h4>", unsafe_allow_html=True)
    trend_data = details["monthly_trend"]
    if trend_data:
        trend_df = pd.DataFrame(trend_data)
        is_dark = st.session_state.get("theme", "light") == "dark"
        grid_color = "#334155" if is_dark else "#E2E8F0"
        chart_font_color = "#94A3B8" if is_dark else "#475569"
        plotly_template = "plotly_dark" if is_dark else "plotly_white"

        fig_trend = go.Figure()
        fig_trend.add_trace(
            go.Bar(
                x=trend_df["month"],
                y=trend_df["spend"],
                name="Spend ($)",
                yaxis="y",
                marker_color="#3B82F6",
                opacity=0.85,
            )
        )
        fig_trend.add_trace(
            go.Scatter(
                x=trend_df["month"],
                y=trend_df["orders"],
                name="Orders Count",
                yaxis="y2",
                line=dict(color="#EF4444", width=3),
                mode="lines+markers",
            )
        )
        fig_trend.update_layout(
            height=260,
            margin=dict(l=10, r=10, t=20, b=10),
            yaxis=dict(title="Spend ($)", side="left", showgrid=True, gridcolor=grid_color),
            yaxis2=dict(title="Orders Count", side="right", overlaying="y", showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Plus Jakarta Sans", size=11, color=chart_font_color),
            template=plotly_template,
        )
        st.plotly_chart(fig_trend, use_container_width=True, theme=None)
    else:
        st.info("No trend data available.")

    st.markdown("<h4>Purchase Order Records</h4>", unsafe_allow_html=True)
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
            column_config={
                "Value ($)": st.column_config.NumberColumn(format="$%,.2f")
            },
            width="stretch",
            hide_index=True,
            use_container_width=True
        )


def render_comparison_tab(table):
    st.markdown("<h3 style='margin-top:0.5rem;'>Side-by-Side Vendor Comparison</h3>", unsafe_allow_html=True)

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
    st.markdown("<h4>Risk Score Comparison</h4>", unsafe_allow_html=True)
    is_dark = st.session_state.get("theme", "light") == "dark"
    grid_color = "#334155" if is_dark else "#E2E8F0"
    chart_font_color = "#94A3B8" if is_dark else "#475569"
    plotly_template = "plotly_dark" if is_dark else "plotly_white"

    fig_comp = px.bar(
        comp_df,
        x="vendor_name",
        y="risk_score",
        color="risk_level",
        hover_data=["on_time_rate", "avg_delay_days"],
        color_discrete_map={"High": "#EF4444", "Medium": "#F59E0B", "Low": "#10B981"},
        labels={"vendor_name": "Vendor", "risk_score": "Risk Score"},
        template=plotly_template,
    )
    fig_comp.update_layout(
        height=260, 
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=grid_color),
        font=dict(family="Plus Jakarta Sans", size=11, color=chart_font_color),
    )
    st.plotly_chart(fig_comp, use_container_width=True, theme=None)

    # 2. Side-by-side Table
    st.markdown("<h4>Key Statistics Breakdown</h4>", unsafe_allow_html=True)
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
        column_config={
            "Risk Score": st.column_config.ProgressColumn("Risk Score", min_value=0, max_value=100, format="%d%%"),
        },
        width="stretch",
        hide_index=True,
        use_container_width=True
    )


def main():
    st.markdown(VENDOR_360_CSS, unsafe_allow_html=True)

    # ---------------------------------------------------------------------------
    # HEADER BANNER
    # ---------------------------------------------------------------------------
    st.markdown(
        """<div class="vendor-banner">
<div class="vendor-banner-title">👥 Vendor Performance Intelligence</div>
<div class="vendor-banner-sub">
Monitor vendor reliability indices, average shipping lag times, and side-by-side metric comparisons.
</div>
</div>""",
        unsafe_allow_html=True,
    )

    @st.cache_data(ttl=300, show_spinner=False)
    def _cached_vendor_risk():
        return get_vendor_risk_table()

    table = _cached_vendor_risk()

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
