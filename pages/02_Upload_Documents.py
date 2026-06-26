import streamlit as st
from pathlib import Path
from src.database import get_procurement_facts, list_documents, count_rows
from src.document_loader import seed_sample_documents, store_document

# ---------------------------------------------------------------------------
# Styling for Document Intelligence Center
# ---------------------------------------------------------------------------
UPLOAD_DOCS_CSS = """
<style>
.doc-intel-banner {
    background: linear-gradient(135deg, #0F172A, #1E293B);
    color: #ffffff;
    border-radius: 14px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
}
.doc-intel-title {
    font-size: 1.3rem;
    font-weight: 800;
    margin-bottom: 0.3rem;
}
.doc-intel-sub {
    font-size: 0.88rem;
    opacity: 0.9;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.stat-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.2rem;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03);
    text-align: center;
}
.stat-card-title {
    font-size: 0.72rem;
    text-transform: uppercase;
    color: var(--text-color);
    opacity: 0.7;
    font-weight: 600;
    margin-bottom: 0.4rem;
}
.stat-card-val {
    font-size: 1.6rem;
    font-weight: 800;
    color: var(--text-color);
}

.preview-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 0.75rem;
    margin: 0.8rem 0 1.5rem 0;
}
.fact-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 0.85rem 1rem;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03);
    transition: all 0.2s ease;
}
.fact-card:hover {
    border-color: var(--primary-blue);
    transform: translateY(-1px);
}

/* Make file uploader highly visible and themed */
div[data-testid="stFileUploader"] {
    background-color: var(--card-bg) !important;
    border: 2px dashed var(--border-color) !important;
    border-radius: 12px !important;
    padding: 0.2rem !important;
    transition: border-color 0.25s ease, background-color 0.25s ease !important;
}
div[data-testid="stFileUploader"]:hover {
    border-color: var(--primary-blue) !important;
    background-color: rgba(79, 140, 255, 0.04) !important;
}
div[data-testid="stFileUploader"] section {
    background-color: transparent !important;
    border: none !important;
}
div[data-testid="stFileUploader"] label, 
div[data-testid="stFileUploader"] div,
div[data-testid="stFileUploader"] span {
    color: var(--text-color) !important;
}
div[data-testid="stFileUploader"] button {
    background-color: var(--primary-blue) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 6px rgba(79, 140, 255, 0.15) !important;
    transition: background-color 0.2s ease !important;
}
div[data-testid="stFileUploader"] button:hover {
    background-color: #3b7ad6 !important;
}
.fact-title {
    font-size: 0.75rem;
    text-transform: uppercase;
    color: var(--text-color);
    opacity: 0.7;
    font-weight: 600;
    margin-bottom: 0.25rem;
}
.fact-value {
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--text-color);
    word-break: break-word;
}
.fact-confidence {
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 6px;
    display: inline-block;
    margin-top: 0.5rem;
}
.conf-high { background: rgba(16, 185, 129, 0.08); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.2); }
.conf-medium { background: rgba(245, 158, 11, 0.08); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.2); }
.conf-low { background: rgba(239, 68, 68, 0.08); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.2); }
</style>
"""


def _render_facts_cards(facts: list[dict]) -> None:
    """Render extracted procurement facts in premium visual grid cards."""
    if not facts:
        return

    st.markdown("<h4>📋 Newly Extracted Procurement Facts</h4>", unsafe_allow_html=True)
    
    fact_cards_html = '<div class="preview-grid">'
    for f in facts:
        conf = f.get("confidence", "medium").lower()
        conf_class = f"conf-{conf}"
        conf_label = conf.title()
        
        fact_cards_html += f"""<div class="fact-card">
<div class="fact-title">{f.get('field', '')}</div>
<div class="fact-value">{f.get('value', '')}</div>
<span class="fact-confidence {conf_class}">{conf_label} Confidence</span>
</div>"""
    fact_cards_html += "</div>"
    st.markdown(fact_cards_html, unsafe_allow_html=True)


def main():
    st.title("Document Intelligence Center")
    st.markdown(UPLOAD_DOCS_CSS, unsafe_allow_html=True)

    # ---------------------------------------------------------------------------
    # HEADER BANNER
    # ---------------------------------------------------------------------------
    st.markdown(
        """<div class="doc-intel-banner">
<div class="doc-intel-title">📂 Document Intelligence Center</div>
<div class="doc-intel-sub">
Upload Purchase Orders, vendor contracts, schedule sheets, and invoices to automatically parse critical procurement parameters.
</div>
</div>""",
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------------------------
    # STATISTICS GRID
    # ---------------------------------------------------------------------------
    docs = list_documents()
    all_facts = get_procurement_facts()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""<div class="stat-card">
<div class="stat-card-title">Indexed Documents</div>
<div class="stat-card-val">{len(docs)}</div>
</div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""<div class="stat-card">
<div class="stat-card-title">Extracted Facts</div>
<div class="stat-card-val">{len(all_facts)}</div>
</div>""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """<div class="stat-card">
<div class="stat-card-title">Supported Extensions</div>
<div class="stat-card-val" style="font-size:1.15rem; padding:0.4rem 0;">PDF, CSV, TXT, Excel</div>
</div>""",
            unsafe_allow_html=True,
        )

    # ---------------------------------------------------------------------------
    # ACTIONS: UPLOAD & SEED
    # ---------------------------------------------------------------------------
    st.subheader("Upload Documents")
    
    col_uploader, col_seeder = st.columns([3, 1])
    
    with col_seeder:
        st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        if st.button("Index Sample Documents", key="seed_btn"):
            with st.spinner("Seeding sample procurement data..."):
                seeded = seed_sample_documents()
                if seeded:
                    st.cache_data.clear()
                    st.success(f"Indexed {len(seeded)} sample documents.")
                else:
                    st.info("Sample documents are already indexed.")

    with col_uploader:
        uploaded_files = st.file_uploader(
            "Drag and drop documents here or browse files",
            type=["pdf", "csv", "txt", "md", "xlsx", "xls"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )

    if uploaded_files:
        st.write("---")
        for uploaded in uploaded_files:
            progress_bar = st.progress(0, text=f"Analyzing {uploaded.name}...")
            try:
                progress_bar.progress(30, text="Reading raw text...")
                doc_bytes = uploaded.read()
                
                progress_bar.progress(60, text="Extracting structure and metadata...")
                doc_id, facts = store_document(uploaded.name, doc_bytes)
                st.cache_data.clear()
                
                progress_bar.progress(100, text="Analysis complete!")
                st.success(f"Successfully processed {uploaded.name} (ID: {doc_id})")
                
                if facts:
                    _render_facts_cards(facts)
                else:
                    st.info("Document loaded successfully. No structured facts were identified.")
            except Exception as exc:
                progress_bar.empty()
                st.error(f"Error parsing {uploaded.name}: {exc}")

    # ---------------------------------------------------------------------------
    # DATA VIEWS
    # ---------------------------------------------------------------------------
    st.write("---")
    tab_facts, tab_docs = st.columns(2)
    
    with tab_facts:
        st.subheader("📊 Extracted Procurement Directory")
        if all_facts:
            st.dataframe(
                [
                    {
                        "Document": row["filename"],
                        "Field": row["field_name"],
                        "Value": row["field_value"],
                        "Confidence": row["confidence"].title() if row["confidence"] else "Medium",
                    }
                    for row in all_facts
                ],
                column_config={
                    "Document": st.column_config.TextColumn("Source File"),
                    "Field": st.column_config.TextColumn("Parameter"),
                    "Value": st.column_config.TextColumn("Value"),
                    "Confidence": st.column_config.TextColumn("Confidence"),
                },
                width="stretch",
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("No extracted facts available in database.")
            
    with tab_docs:
        st.subheader("📄 Indexed Repository")
        if docs:
            st.dataframe(
                [
                    {
                        "Document ID": row["id"],
                        "Filename": row["filename"],
                        "Chunks": row["chunk_count"],
                        "Uploaded": row["uploaded_at"],
                    }
                    for row in docs
                ],
                column_config={
                    "Document ID": st.column_config.NumberColumn("ID"),
                    "Filename": st.column_config.TextColumn("Filename"),
                    "Chunks": st.column_config.NumberColumn("Chunks"),
                    "Uploaded": st.column_config.TextColumn("Uploaded Timestamp"),
                },
                width="stretch",
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("No documents indexed in repository yet.")


if __name__ == "__main__":
    main()
