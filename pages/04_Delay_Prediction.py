import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
from src.database import save_prediction
from src.delay_model import (
    get_delivery_risk_table,
    load_procurement_data,
    predict_delay_risk,
    _joblib_models_available,
)

# ---------------------------------------------------------------------------
# Styling for Delay Prediction Cockpit
# ---------------------------------------------------------------------------
COCKPIT_CSS = """
<style>
.cockpit-banner {
    background: linear-gradient(135deg, #0F172A, #1E293B);
    color: #ffffff;
    border-radius: 14px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
}
.cockpit-title {
    font-size: 1.3rem;
    font-weight: 800;
    margin-bottom: 0.3rem;
}
.cockpit-sub {
    font-size: 0.88rem;
    opacity: 0.9;
}

/* Result panel custom styling */
.result-panel {
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1.5rem 0;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
}
.panel-High {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.12), rgba(239, 68, 68, 0.05));
    border: 1px solid rgba(239, 68, 68, 0.25);
    border-left: 5px solid #EF4444;
}
.panel-Medium {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.12), rgba(245, 158, 11, 0.05));
    border: 1px solid rgba(245, 158, 11, 0.25);
    border-left: 5px solid #F59E0B;
}
.panel-Low {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(16, 185, 129, 0.05));
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-left: 5px solid #10B981;
}

.result-title {
    font-size: 1.25rem;
    font-weight: 800;
    margin-bottom: 0.8rem;
}
.title-High { color: #EF4444; }
.title-Medium { color: #F59E0B; }
.title-Low { color: #10B981; }

/* Horizontal Timeline component */
.timeline-horiz {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin: 1rem 0;
}
.time-node {
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--text-color);
    opacity: 0.75;
    text-transform: uppercase;
    text-align: center;
    position: relative;
    flex: 1;
}
.time-node-val {
    font-size: 0.88rem;
    font-weight: 800;
    color: var(--text-color);
    margin-top: 0.3rem;
}
.time-node-predicted .time-node-val {
    color: #EF4444;
}

/* Recommendation action box */
.recom-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 1.1rem 1.3rem;
    margin-top: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}
.recom-header {
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    color: #3B82F6;
    letter-spacing: 0.05em;
    margin-bottom: 0.4rem;
}
.recom-body {
    font-size: 0.88rem;
    color: var(--text-color);
    line-height: 1.5;
}
</style>
"""


@st.cache_data(ttl=300, show_spinner=False)
def _cached_procurement_data():
    return load_procurement_data()


@st.cache_data(ttl=300, show_spinner=False)
def _cached_delivery_risk():
    return get_delivery_risk_table()


def main():
    st.title("Delay Prediction Cockpit")
    st.markdown(COCKPIT_CSS, unsafe_allow_html=True)

    data = _cached_procurement_data()
    vendors = sorted(data["vendor_name"].unique())
    materials = sorted(data["material_name"].unique())
    phases = sorted(data["project_phase"].unique())

    # Safely pick default indices
    default_material_idx = 0
    for i, m in enumerate(materials):
        if "steel" in m.lower() or "cement" in m.lower():
            default_material_idx = i
            break

    default_vendor_idx = 0
    for i, v in enumerate(vendors):
        if "zenith" in v.lower() or "canyon" in v.lower():
            default_vendor_idx = i
            break

    # ---------------------------------------------------------------------------
    # HEADER BANNER
    # ---------------------------------------------------------------------------
    st.markdown(
        """<div class="cockpit-banner">
<div class="cockpit-title">🔮 Machine Learning Delay Prediction</div>
<div class="cockpit-sub">
Run predictive machine learning models to identify future material lead time delays and evaluate float consumption risk.
</div>
</div>""",
        unsafe_allow_html=True,
    )

    if _joblib_models_available():
        st.success("🧠 Active Inference: Using pre-trained Machine Learning (joblib) models.")
    else:
        st.info("⚙️ Active Inference: Using on-the-fly dynamically trained pipeline models.")

    # ---------------------------------------------------------------------------
    # INPUT COCKPIT FORM
    # ---------------------------------------------------------------------------
    with st.form("delay_prediction_form"):
        st.subheader("📋 Predict Material Delivery Risk Parameters")
        
        col1, col2, col3 = st.columns(3)
        material = col1.selectbox("Material Name", materials, index=default_material_idx)
        vendor = col2.selectbox("Vendor Name", vendors, index=default_vendor_idx)
        quantity = col3.number_input("Quantity Required", min_value=1.0, value=120.0, step=5.0)

        col4, col5, col6 = st.columns(3)
        order_date = col4.date_input("Purchase Order Date")
        promised_date = col5.date_input("Promised Delivery Date")
        priority = col6.selectbox("Material Priority", ["Critical", "High", "Medium", "Low"], index=0)

        project_phase = st.selectbox(
            "Target Project Phase",
            phases,
            index=0,
        )
        
        submitted = st.form_submit_button("Generate Prediction Profile")

    # ---------------------------------------------------------------------------
    # PREDICTION COCKPIT RESULTS
    # ---------------------------------------------------------------------------
    if submitted:
        prediction = predict_delay_risk(
            material_name=material,
            vendor_name=vendor,
            order_date=str(order_date),
            promised_delivery_date=str(promised_date),
            quantity=quantity,
            priority=priority,
            project_phase=project_phase,
        )
        save_prediction(prediction)

        risk_level = prediction["risk_level"]
        risk_score = prediction["risk_score"]
        expected_delay = prediction["expected_delay_days"]
        expected_roj = prediction["expected_roj_date"]
        
        # Display the custom styled prediction cockpit panel
        st.markdown(
            f"""<div class="result-panel panel-{risk_level}">
<div class="result-title title-{risk_level}">
{"🔴" if risk_level == "High" else "🟡" if risk_level == "Medium" else "🟢"}
{risk_level.upper()} RISK DETECTED ({risk_score}% Severity)
</div>
</div>""",
            unsafe_allow_html=True,
        )

        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            # Prediction confidence gauge
            st.markdown("<h4 style='text-align:center;'>Risk Severity Level</h4>", unsafe_allow_html=True)
            is_dark = st.session_state.get("theme", "light") == "dark"
            tick_color = "#94A3B8" if is_dark else "#64748B"
            num_color = "#FFFFFF" if is_dark else "#0F172A"
            fig_conf = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=risk_score,
                    gauge={
                        "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": tick_color},
                        "bar": {"color": "#EF4444" if risk_level == "High" else "#F59E0B" if risk_level == "Medium" else "#10B981"},
                        "steps": [
                            {"range": [0, 35], "color": "rgba(16, 185, 129, 0.08)"},
                            {"range": [35, 60], "color": "rgba(245, 158, 11, 0.08)"},
                            {"range": [60, 100], "color": "rgba(239, 68, 68, 0.08)"},
                        ],
                    },
                    number={"suffix": "%", "font": {"family": "Plus Jakarta Sans", "weight": "bold", "color": num_color}},
                )
            )
            fig_conf.update_layout(
                height=150,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_conf, use_container_width=True)
            
            st.metric("Expected Lead-Time Delay", f"{expected_delay} days")

        with col_right:
            # Timeline showing promised vs expected ROJ
            st.markdown("<h4>📅 Expected Milestone Timeline</h4>", unsafe_allow_html=True)
            st.markdown(
                f"""<div class="timeline-horiz">
<div class="time-node">
Ordered
<div class="time-node-val">{order_date}</div>
</div>
<div class="time-node">
Promised
<div class="time-node-val">{promised_date}</div>
</div>
<div class="time-node time-node-predicted">
Est. Delivery
<div class="time-node-val">{expected_roj}</div>
</div>
</div>""",
                unsafe_allow_html=True,
            )

            # Recommendations action card
            st.markdown(
                f"""<div class="recom-card">
<div class="recom-header">⚡ Strategic Recommendation & Mitigation</div>
<div class="recom-body">{prediction['recommendation']}</div>
</div>""",
                unsafe_allow_html=True,
            )

    # ---------------------------------------------------------------------------
    # OPEN ORDER RISK MAP
    # ---------------------------------------------------------------------------
    st.write("---")
    st.subheader("Current Open Orders Risk Matrix")
    
    risk_table = _cached_delivery_risk()
    
    is_dark = st.session_state.get("theme", "light") == "dark"
    grid_color = "#334155" if is_dark else "#E2E8F0"
    chart_font_color = "#94A3B8" if is_dark else "#475569"
    plotly_template = "plotly_dark" if is_dark else "plotly_white"

    fig = px.scatter(
        risk_table,
        x="promised_delivery_date",
        y="risk_score",
        size="contract_value",
        color="risk_level",
        hover_data=["po_number", "material_name", "vendor_name", "expected_roj_date"],
        color_discrete_map={"High": "#EF4444", "Medium": "#F59E0B", "Low": "#10B981"},
        labels={"promised_delivery_date": "Promised Delivery Date", "risk_score": "Risk Severity Score", "risk_level": "Risk Level"},
        title="Open Purchase Orders: Risk Profile vs. promised delivery",
        template=plotly_template,
    )
    fig.update_layout(
        yaxis_title="Risk Score", 
        xaxis_title="Promised Delivery Date", 
        height=320,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor=grid_color),
        yaxis=dict(showgrid=True, gridcolor=grid_color),
        font=dict(family="Plus Jakarta Sans", size=11, color=chart_font_color),
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(
        risk_table[[
            "po_number", "material_name", "vendor_name", "promised_delivery_date", "expected_roj_date", "risk_level", "risk_score", "expected_delay_days", "contract_value"
        ]].rename(
            columns={
                "po_number": "PO #",
                "material_name": "Material",
                "vendor_name": "Vendor",
                "promised_delivery_date": "Promised Date",
                "expected_roj_date": "Predicted Delivery",
                "risk_level": "Risk Tier",
                "risk_score": "Risk Score",
                "expected_delay_days": "Delay (Days)",
                "contract_value": "Value ($)"
            }
        ),
        column_config={
            "Risk Score": st.column_config.ProgressColumn("Risk Score", min_value=0, max_value=100, format="%d%%"),
            "Value ($)": st.column_config.NumberColumn("Value", format="$%,.2f"),
        },
        width="stretch",
        hide_index=True,
        use_container_width=True
    )


if __name__ == "__main__":
    main()
