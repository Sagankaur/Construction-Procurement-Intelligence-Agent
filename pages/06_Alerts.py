import streamlit as st

from src.alerts import alert_counts, generate_alerts
from src.delay_model import get_delivery_risk_table
from src.vendor_risk import get_vendor_risk_table

# Premium CSS styling for Alert Control Center
ALERTS_CSS = """
<style>
.alerts-banner {
    background: linear-gradient(135deg, #0F172A, #1E293B);
    color: #ffffff;
    border-radius: 14px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.05);
}
.alerts-banner-title {
    font-size: 1.3rem;
    font-weight: 800;
    margin-bottom: 0.3rem;
}
.alerts-banner-sub {
    font-size: 0.88rem;
    color: #94a3b8;
}

/* Alert boxes */
.alert-box {
    background: var(--card-bg);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.2rem;
    border: 1px solid var(--border-color);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
    transition: all 0.2s ease;
}
.alert-box:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
}

.alert-Critical { border-left: 5px solid #EF4444; }
.alert-High { border-left: 5px solid #F59E0B; }
.alert-Medium { border-left: 5px solid #3B82F6; }
.alert-Low { border-left: 5px solid #10B981; }

.alert-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.6rem;
}
.alert-badge {
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 6px;
    text-transform: uppercase;
    letter-spacing: 0.02em;
}
.badge-Critical { background: rgba(239, 68, 68, 0.08); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.2); }
.badge-High { background: rgba(245, 158, 11, 0.08); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.2); }
.badge-Medium { background: rgba(59, 130, 246, 0.08); color: #3B82F6; border: 1px solid rgba(59, 130, 246, 0.2); }
.badge-Low { background: rgba(16, 185, 129, 0.08); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.2); }

.alert-title {
    font-weight: 700;
    font-size: 1.05rem;
    color: var(--text-color);
}
.alert-detail {
    font-size: 0.88rem;
    color: var(--text-color);
    opacity: 0.9;
    line-height: 1.5;
    margin-bottom: 0.8rem;
}
.alert-action-box {
    background: var(--bg-color);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 0.8rem 1.1rem;
    font-size: 0.85rem;
    color: var(--text-color);
    margin-bottom: 0.6rem;
}
.alert-action-box b {
    color: #3B82F6;
    font-weight: 600;
}
.alert-due {
    font-size: 0.78rem;
    color: #94a3b8;
    font-weight: 500;
}
</style>
"""



@st.cache_data(ttl=300, show_spinner=False)
def _cached_delivery_risk():
    return get_delivery_risk_table()


@st.cache_data(ttl=300, show_spinner=False)
def _cached_vendor_risk():
    return get_vendor_risk_table()


def main():
    st.title("Procurement Alerts")
    st.markdown(ALERTS_CSS, unsafe_allow_html=True)

    # ---------------------------------------------------------------------------
    # HEADER BANNER
    # ---------------------------------------------------------------------------
    st.markdown(
        """<div class="alerts-banner">
<div class="alerts-banner-title">🚨 Alert Control Center</div>
<div class="alerts-banner-sub">
Real-time critical path notifications, material delivery exceptions, and vendor risk triggers needing immediate mitigation.
</div>
</div>""",
        unsafe_allow_html=True,
    )

    delivery_risk = _cached_delivery_risk()
    vendor_risk = _cached_vendor_risk()
    counts = alert_counts(delivery_risk=delivery_risk, vendor_risk=vendor_risk)

    # Stats counters
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔴 Critical Path Blocked", counts.get("Critical", 0))
    col2.metric("🟠 High Risk Exception", counts.get("High", 0))
    col3.metric("🟡 Medium Delay warning", counts.get("Medium", 0))
    col4.metric("🟢 Low / Within Float", counts.get("Low", 0))

    st.write("---")

    # Interactive Severity Filter
    st.subheader("Actionable Alerts Feed")
    severity_filter = st.multiselect(
        "Filter alerts by severity level:",
        ["Critical", "High", "Medium", "Low"],
        default=["Critical", "High", "Medium"],
    )

    alerts = generate_alerts(delivery_risk=delivery_risk, vendor_risk=vendor_risk)
    filtered_alerts = [a for a in alerts if a["severity"] in severity_filter]

    if not filtered_alerts:
        st.info("No active alerts found matching the selected severity filters.")
        return

    # Render filtered alerts using premium custom HTML boxes
    for alert in filtered_alerts:
        sev = alert["severity"]
        due_info = ""
        if alert.get("due_date"):
            due_info = f"""<div class="alert-due">
📅 Target Mitigation Due Date: <b>{alert['due_date']}</b>
</div>"""
            
        st.markdown(
            f"""<div class="alert-box alert-{sev}">
<div class="alert-header">
<span class="alert-badge badge-{sev}">{sev}</span>
<span class="alert-title">{alert['title']}</span>
</div>
<div class="alert-detail">{alert['detail']}</div>
<div class="alert-action-box">
<b>Recommended Mitigation:</b> {alert['action']}
</div>
{due_info}
</div>""",
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
