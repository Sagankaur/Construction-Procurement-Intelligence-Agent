import streamlit as st

from src.document_loader import seed_sample_documents
from src.rag_engine import RAGResponse, get_answer

DEMO_QUESTIONS = [
    "Which deliveries are at risk this month?",
    "Which vendors are high risk?",
    "What purchase orders need follow-up?",
    "What materials are delayed?",
    "What is the expected ROJ date for steel?",
    "Which critical materials may affect the project schedule?",
]


def _render_source_cards(response: RAGResponse) -> None:
    """Render visual source cards under the AI response."""
    if not response.sources:
        return

    st.markdown(
        """
        <div style="
            margin-top: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #d8dee7;
        ">
            <span style="
                font-size: 0.85rem;
                font-weight: 600;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            ">📚 Sources Referenced</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(min(len(response.sources), 2))
    for idx, card in enumerate(response.sources):
        col = cols[idx % len(cols)]
        with col:
            # Score as percentage for display
            score_pct = min(card.score * 100, 100)
            if score_pct >= 70:
                score_color = "#0f766e"
                score_label = "High"
            elif score_pct >= 40:
                score_color = "#b45309"
                score_label = "Medium"
            else:
                score_color = "#64748b"
                score_label = "Low"

            st.markdown(
                f"""
                <div style="
                    background: white;
                    border: 1px solid #e2e8f0;
                    border-radius: 10px;
                    padding: 1rem;
                    margin: 0.5rem 0;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
                    transition: box-shadow 0.2s ease;
                ">
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 0.5rem;
                    ">
                        <span style="
                            font-weight: 600;
                            color: #1e293b;
                            font-size: 0.9rem;
                        ">📄 {card.filename}</span>
                        <span style="
                            background: {score_color}18;
                            color: {score_color};
                            font-size: 0.75rem;
                            font-weight: 600;
                            padding: 2px 8px;
                            border-radius: 12px;
                        ">{score_label} Relevance</span>
                    </div>
                    <div style="
                        font-size: 0.78rem;
                        color: #64748b;
                        margin-bottom: 0.5rem;
                    ">Chunk #{card.chunk_idx} · Score: {card.score:.4f}</div>
                    <div style="
                        background: #f8fafc;
                        border-radius: 6px;
                        padding: 0.6rem 0.8rem;
                        font-size: 0.82rem;
                        color: #334155;
                        line-height: 1.5;
                        border-left: 3px solid {score_color};
                    ">{card.excerpt}</div>
                    <div style="
                        margin-top: 0.5rem;
                        height: 4px;
                        background: #e2e8f0;
                        border-radius: 2px;
                        overflow: hidden;
                    ">
                        <div style="
                            width: {score_pct:.0f}%;
                            height: 100%;
                            background: linear-gradient(90deg, {score_color}, {score_color}aa);
                            border-radius: 2px;
                        "></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


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
            response = get_answer(query)

        # Display the answer
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #0f766e08, #0f766e03);
                border: 1px solid #0f766e30;
                border-radius: 10px;
                padding: 1.2rem 1.5rem;
                margin: 1rem 0;
            ">
                <div style="
                    font-size: 0.8rem;
                    font-weight: 600;
                    color: #0f766e;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    margin-bottom: 0.5rem;
                ">🤖 SiteSage AI Response</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(response.answer)

        # Display source cards
        _render_source_cards(response)
