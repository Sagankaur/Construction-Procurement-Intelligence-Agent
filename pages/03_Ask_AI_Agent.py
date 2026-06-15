import streamlit as st

from src.document_loader import seed_sample_documents
from src.rag_engine import get_answer

DEMO_QUESTIONS = [
    "Which deliveries are at risk this month?",
    "Which vendors are high risk?",
    "What purchase orders need follow-up?",
    "What materials are delayed?",
    "What is the expected ROJ date for steel?",
    "Which critical materials may affect the project schedule?",
]


def main():
    st.title("Ask AI Agent")

    col1, col2 = st.columns([2, 1])
    with col1:
        selected = st.selectbox("Demo question", DEMO_QUESTIONS)
    with col2:
        if st.button("Index Sample Docs", width="stretch"):
            seeded = seed_sample_documents()
            st.success(f"Indexed {len(seeded)} documents." if seeded else "Sample docs already indexed.")

    query = st.text_area("Question", value=selected, height=90)
    if st.button("Ask SiteSage", width="stretch"):
        with st.spinner("Retrieving cited procurement context"):
            answer = get_answer(query)
        st.markdown(answer)
