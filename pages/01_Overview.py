import plotly.express as px
import streamlit as st

from src.alerts import alert_counts, generate_alerts
from src.database import count_rows
from src.delay_model import get_delivery_risk_table, load_procurement_data
from src.vendor_risk import get_vendor_risk_table


def main():
    st.title("SiteSage AI Overview")

    data = load_procurement_data()
    delivery_risk = get_delivery_risk_table()
    vendor_risk = get_vendor_risk_table(data)
    counts = alert_counts()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Indexed Documents", count_rows("documents"))
    col2.metric("Open Purchase Orders", int(data["actual_delivery_date"].isna().sum()))
    col3.metric("High Risk Vendors", int((vendor_risk["risk_level"] == "High").sum()))
    col4.metric("Critical Alerts", counts.get("Critical", 0))

    left, right = st.columns([1.35, 1])
    with left:
        st.subheader("Delivery Risk Pipeline")
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

    with right:
        st.subheader("Top Alerts")
        for alert in generate_alerts()[:5]:
            st.markdown(
                f"**{alert['severity']} - {alert['title']}**  \n"
                f"{alert['detail']}  \n"
                f"Action: {alert['action']}"
            )

    st.subheader("Open Orders Requiring Attention")
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
