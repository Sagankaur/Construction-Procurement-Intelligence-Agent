import plotly.express as px
import streamlit as st

from src.database import save_prediction
from src.delay_model import (
    get_delivery_risk_table,
    load_procurement_data,
    predict_delay_risk,
    _joblib_models_available,
)


def main():
    st.title("Delay Prediction")

    data = load_procurement_data()
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

    # Model source indicator
    if _joblib_models_available():
        st.success("🧠 Using trained ML models (joblib artifacts) for inference")
    else:
        st.info("⚙️ Using on-the-fly trained pipeline (joblib models not found)")

    with st.form("delay_prediction_form"):
        col1, col2, col3 = st.columns(3)
        material = col1.selectbox("Material", materials, index=default_material_idx)
        vendor = col2.selectbox("Vendor", vendors, index=default_vendor_idx)
        quantity = col3.number_input("Quantity", min_value=1.0, value=120.0, step=5.0)

        col4, col5, col6 = st.columns(3)
        order_date = col4.date_input("Order Date")
        promised_date = col5.date_input("Promised Delivery")
        priority = col6.selectbox("Priority", ["Critical", "High", "Medium", "Low"], index=0)

        project_phase = st.selectbox(
            "Project Phase",
            phases,
            index=0,
        )
        submitted = st.form_submit_button("Predict Delay Risk")

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

        # --- Styled result display ---
        risk_color = {
            "High": "#b91c1c",
            "Medium": "#b45309",
            "Low": "#0f766e",
        }.get(prediction["risk_level"], "#64748b")

        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, {risk_color}22, {risk_color}08);
                border-left: 4px solid {risk_color};
                border-radius: 8px;
                padding: 1rem 1.5rem;
                margin: 1rem 0;
            ">
                <h3 style="color: {risk_color}; margin: 0 0 0.5rem 0;">
                    {'🔴' if prediction['risk_level'] == 'High' else '🟡' if prediction['risk_level'] == 'Medium' else '🟢'}
                    {prediction['risk_level']} Risk Detected
                </h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns(3)
        col1.metric("Risk Level", prediction["risk_level"])
        col2.metric("Risk Score", f"{prediction['risk_score']}%")
        col3.metric("Expected Delay", f"{prediction['expected_delay_days']} days")
        st.info(f"Expected ROJ date: {prediction['expected_roj_date']}")
        st.write(prediction["recommendation"])

    risk_table = get_delivery_risk_table()
    st.subheader("Current Open Order Risk")
    fig = px.scatter(
        risk_table,
        x="promised_delivery_date",
        y="risk_score",
        size="contract_value",
        color="risk_level",
        hover_data=["po_number", "material_name", "vendor_name", "expected_roj_date"],
        color_discrete_map={"High": "#b91c1c", "Medium": "#b45309", "Low": "#0f766e"},
    )
    fig.update_layout(yaxis_title="Risk score", xaxis_title="Promised delivery", height=360)
    st.plotly_chart(fig, width="stretch")
    st.dataframe(risk_table, width="stretch", hide_index=True)
