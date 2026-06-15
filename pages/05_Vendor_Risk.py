import plotly.express as px
import streamlit as st

from src.vendor_risk import get_vendor_risk_table


def main():
    st.title("Vendor Risk")

    table = get_vendor_risk_table()
    col1, col2, col3 = st.columns(3)
    col1.metric("Tracked Vendors", len(table))
    col2.metric("High Risk", int((table["risk_level"] == "High").sum()))
    col3.metric("Average On-Time Rate", f"{table['on_time_rate'].mean():.1f}%")

    fig = px.bar(
        table,
        x="vendor_name",
        y="risk_score",
        color="risk_level",
        hover_data=["on_time_rate", "avg_delay_days", "materials"],
        color_discrete_map={"High": "#b91c1c", "Medium": "#b45309", "Low": "#0f766e"},
    )
    fig.update_layout(xaxis_title="", yaxis_title="Risk score", height=360)
    st.plotly_chart(fig, width="stretch")

    st.subheader("Vendor Reliability Scores")
    st.dataframe(table, width="stretch", hide_index=True)
