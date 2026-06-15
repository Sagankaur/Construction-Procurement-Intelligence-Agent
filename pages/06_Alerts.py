import streamlit as st

from src.alerts import alert_counts, generate_alerts


def main():
    st.title("Procurement Alerts")

    counts = alert_counts()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Critical", counts.get("Critical", 0))
    col2.metric("High", counts.get("High", 0))
    col3.metric("Medium", counts.get("Medium", 0))
    col4.metric("Low", counts.get("Low", 0))

    for alert in generate_alerts():
        with st.container(border=True):
            st.subheader(f"{alert['severity']} - {alert['title']}")
            st.write(alert["detail"])
            st.write(f"Action: {alert['action']}")
            if alert.get("due_date"):
                st.caption(f"Due date: {alert['due_date']}")
