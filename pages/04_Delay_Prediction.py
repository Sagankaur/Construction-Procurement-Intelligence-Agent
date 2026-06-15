import plotly.express as px
import streamlit as st

from src.database import save_prediction
from src.delay_model import get_delivery_risk_table, load_procurement_data, predict_delay_risk


def main():
    st.title("Delay Prediction")

    data = load_procurement_data()
    vendors = sorted(data["vendor_name"].unique())
    materials = sorted(data["material_name"].unique())
    phases = sorted(data["project_phase"].unique())

    with st.form("delay_prediction_form"):
        col1, col2, col3 = st.columns(3)
        material = col1.selectbox("Material", materials, index=materials.index("Structural Steel"))
        vendor = col2.selectbox("Vendor", vendors, index=vendors.index("ABC Metals"))
        quantity = col3.number_input("Quantity", min_value=1.0, value=120.0, step=5.0)

        col4, col5, col6 = st.columns(3)
        order_date = col4.date_input("Order Date", value=data["order_date"].min().date())
        promised_date = col5.date_input("Promised Delivery", value=data["promised_delivery_date"].max().date())
        priority = col6.selectbox("Priority", ["Critical", "High", "Medium", "Low"], index=0)

        project_phase = st.selectbox(
            "Project Phase",
            phases,
            index=phases.index("Superstructure"),
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
