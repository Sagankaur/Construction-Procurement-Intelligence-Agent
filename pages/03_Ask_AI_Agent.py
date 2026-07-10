import streamlit as st
from src.document_loader import seed_sample_documents
from src.rag_engine import RAGResponse, get_answer

# ---------------------------------------------------------------------------
# Styling for AI Copilot Chat Interface
# ---------------------------------------------------------------------------
COPILOT_CSS = """
<style>
.copilot-banner {
    background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
    border: 1px solid #FFCC80;
    border-radius: 14px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 12px rgba(255, 152, 0, 0.05);
}
.copilot-title {
    font-size: 1.3rem;
    font-weight: 800;
    margin-bottom: 0.3rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #07315F !important;
}
.copilot-sub {
    font-size: 0.88rem;
    color: #4A5568 !important;
}

/* Chat bubble styling */
.chat-container {
    margin: 1.5rem 0;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}
.chat-bubble {
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    max-width: 85%;
    line-height: 1.6;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03);
}
.chat-bubble-user {
    align-self: flex-end;
    background-color: var(--bg-color);
    color: var(--text-color);
    border: 1px solid var(--border-color);
    border-bottom-right-radius: 2px;
}
.chat-bubble-ai {
    align-self: flex-start;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.04), rgba(59, 130, 246, 0.01));
    color: var(--text-color);
    border: 1px solid rgba(59, 130, 246, 0.18);
    border-left: 4px solid #3B82F6;
    border-bottom-left-radius: 2px;
}
.bubble-meta {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.4rem;
}
.meta-user { color: #64748b; }
.meta-ai { color: #3B82F6; }

.source-header {
    margin-top: 2rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-color);
}
.source-header-title {
    font-size: 0.82rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.source-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 1.1rem;
    margin: 0.6rem 0;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
    transition: all 0.2s ease;
}
.source-card:hover {
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    border-color: var(--primary-blue);
}
.source-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}
.source-file {
    font-weight: 700;
    color: var(--text-color);
    font-size: 0.88rem;
}
.source-badge {
    font-size: 0.7rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 6px;
    text-transform: uppercase;
}
.badge-high { background: rgba(16, 185, 129, 0.08); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.2); }
.badge-medium { background: rgba(245, 158, 11, 0.08); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.2); }
.badge-low { background: rgba(100, 116, 139, 0.08); color: #64748B; border: 1px solid rgba(100, 116, 139, 0.2); }

.source-meta {
    font-size: 0.76rem;
    color: #94a3b8;
    margin-bottom: 0.5rem;
}
.source-excerpt {
    background: var(--bg-color);
    border-radius: 6px;
    padding: 0.7rem 0.9rem;
    font-size: 0.82rem;
    color: var(--text-color);
    line-height: 1.5;
    border-left: 3px solid var(--border-color);
}

/* Redesign Suggested Inquiry buttons into sleek premium outlined pills by targeting column buttons */
div[data-testid="column"] button {
    background-color: var(--card-bg) !important;
    color: var(--text-color) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 30px !important;
    padding: 0.45rem 1.25rem !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
div[data-testid="column"] button:hover {
    border-color: var(--primary-blue) !important;
    background-color: rgba(79, 140, 255, 0.04) !important;
    color: var(--primary-blue) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(79, 140, 255, 0.08) !important;
}

/* Redesign secondary button (Re-Index Sample Docs) at the bottom to be rectangular secondary button */
div:has(> .secondary-button-marker) + div.element-container button {
    background-color: var(--card-bg) !important;
    color: var(--text-color) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
    transition: all 0.2s ease !important;
    padding: 0.6rem 1.2rem !important;
}
div:has(> .secondary-button-marker) + div.element-container button:hover {
    border-color: var(--primary-blue) !important;
    background-color: rgba(79, 140, 255, 0.04) !important;
    color: var(--primary-blue) !important;
}

/* Redesign primary submit button at the bottom to be filled blue with white text */
div:has(> .primary-button-marker) + div.element-container button {
    background-color: var(--primary-blue) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--primary-blue) !important;
    border-radius: 8px !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.2rem !important;
    box-shadow: 0 4px 6px rgba(79, 140, 255, 0.15) !important;
    transition: all 0.2s ease !important;
}
div:has(> .primary-button-marker) + div.element-container button:hover {
    background-color: #2563EB !important;
    border-color: #2563EB !important;
    color: #FFFFFF !important;
}

/* Global widget label formatting for maximum readability in both themes */
label[data-testid="stWidgetLabel"],
label[data-testid="stWidgetLabel"] p {
    color: var(--primary-navy) !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    opacity: 1 !important;
    letter-spacing: -0.015em !important;
    margin-bottom: 0.35rem !important;
}

.copilot-section-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--primary-navy);
    margin-bottom: 0.5rem;
    margin-top: 1.5rem;
}
</style>
"""

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
        """<div class="source-header">
<span class="source-header-title">📚 Citation Directory & Evidence Base</span>
</div>""",
        unsafe_allow_html=True,
    )

    cols = st.columns(min(len(response.sources), 2))
    for idx, card in enumerate(response.sources):
        col = cols[idx % len(cols)]
        with col:
            score_pct = min(card.score * 100, 100)
            if score_pct >= 70:
                score_class = "badge-high"
                score_label = "High Relevance"
            elif score_pct >= 40:
                score_class = "badge-medium"
                score_label = "Medium Relevance"
            else:
                score_class = "badge-low"
                score_label = "Low Relevance"

            with st.container():
                st.markdown(
                    f"""<div class="source-card">
<div class="source-card-header">
<span class="source-file">📄 {card.filename}</span>
<span class="source-badge {score_class}">{score_label}</span>
</div>
<div class="source-meta">
Chunk #{card.chunk_idx} • Score: {card.score:.4f} ({score_pct:.1f}%)
</div>
<div class="source-excerpt">
{card.excerpt}
</div>
</div>""",
                    unsafe_allow_html=True,
                )


def main():
    st.markdown(COPILOT_CSS, unsafe_allow_html=True)

    # ---------------------------------------------------------------------------
    # HEADER BANNER
    # ---------------------------------------------------------------------------
    st.markdown(
        """<div class="copilot-banner">
<div class="copilot-title"> SiteSage AI Copilot</div>
<div class="copilot-sub">
Ask natural language questions regarding lead times, vendor risk tiers, and critical milestones extracted from indexed files.
</div>
</div>""",
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------------------------
    # DEMO QUESTIONS BAR
    # ---------------------------------------------------------------------------
    st.markdown('<p class="copilot-section-title">Select a Suggested Inquiry:</p>', unsafe_allow_html=True)
    st.markdown('<div class="suggested-inquiries-marker"></div>', unsafe_allow_html=True)
    
    # Render suggested tags as columns
    cols_sug = st.columns(3)
    sug_q1 = cols_sug[0].button("📅 Steel ROJ Date", use_container_width=True)
    sug_q2 = cols_sug[1].button("⚠️ At-Risk Deliveries", use_container_width=True)
    sug_q3 = cols_sug[2].button("👥 High-Risk Vendors", use_container_width=True)

    selected_query = ""
    if sug_q1:
        selected_query = "What is the expected ROJ date for steel?"
    elif sug_q2:
        selected_query = "Which deliveries are at risk this month?"
    elif sug_q3:
        selected_query = "Which vendors are high risk?"

    # ---------------------------------------------------------------------------
    # COPTILOT INPUT
    # ---------------------------------------------------------------------------
    if "copilot_input" not in st.session_state:
        st.session_state.copilot_input = DEMO_QUESTIONS[0]

    if selected_query:
        st.session_state.copilot_input = selected_query

    # Query Selector dropdown
    dropdown_query = st.selectbox("Or choose a pre-loaded question:", DEMO_QUESTIONS, index=0)
    
    # If selectbox changes and no suggested query was pressed, use selectbox
    query_value = selected_query if selected_query else dropdown_query

    query = st.text_area("Your Question", value=query_value, height=80)

    # Bottom buttons
    col_submit, col_seed = st.columns([3, 1])
    with col_seed:
        st.markdown('<div class="secondary-button-marker"></div>', unsafe_allow_html=True)
        if st.button("Re-Index Sample Docs", use_container_width=True):
            with st.spinner("Seeding sample documents..."):
                seeded = seed_sample_documents()
                if seeded:
                    st.cache_data.clear()
                    st.success(f"Indexed {len(seeded)} documents.")
                else:
                    st.info("Sample documents already indexed.")
                    
    with col_submit:
        st.markdown('<div class="primary-button-marker"></div>', unsafe_allow_html=True)
        submitted = st.button("Ask SiteSage AI", use_container_width=True)

    if submitted and query:
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        
        # User bubble
        st.markdown(
            f"""<div class="chat-bubble chat-bubble-user">
<div class="bubble-meta meta-user">👤 Project Manager</div>
{query}
</div>""",
            unsafe_allow_html=True,
        )
        
        # Call RAG engine
        with st.spinner("Retrieving cited procurement context..."):
            response = get_answer(query)
            
        # AI bubble
        st.markdown(
            f"""<div class="chat-bubble chat-bubble-ai">
<div class="bubble-meta meta-ai">🤖 SiteSage AI Copilot</div>
{response.answer}
</div>""",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # Source citations
        _render_source_cards(response)


if __name__ == "__main__":
    main()
