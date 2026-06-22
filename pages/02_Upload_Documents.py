import streamlit as st

from src.database import get_procurement_facts, list_documents
from src.document_loader import seed_sample_documents, store_document


def _render_facts_table(facts: list[dict]) -> None:
    """Render extracted procurement facts as a styled table."""
    if not facts:
        return

    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #0f766e12, #0f766e06);
            border: 1px solid #0f766e40;
            border-radius: 10px;
            padding: 1rem 1.5rem;
            margin: 0.5rem 0 1rem 0;
        ">
            <h4 style="color: #0f766e; margin: 0 0 0.5rem 0;">
                📋 Extracted Procurement Facts
            </h4>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.dataframe(
        [
            {
                "Field": f.get("field", ""),
                "Extracted Value": f.get("value", ""),
                "Confidence": f.get("confidence", "medium").title(),
            }
            for f in facts
        ],
        width="stretch",
        hide_index=True,
        column_config={
            "Field": st.column_config.TextColumn("Field", width="small"),
            "Extracted Value": st.column_config.TextColumn("Value", width="medium"),
            "Confidence": st.column_config.TextColumn("Confidence", width="small"),
        },
    )


def main():
    st.title("Upload Procurement Documents")

    controls = st.columns([1, 2])
    with controls[0]:
        if st.button("Load Sample Documents", width="stretch"):
            seeded = seed_sample_documents()
            if seeded:
                st.success(f"Indexed {len(seeded)} sample documents.")
            else:
                st.info("Sample documents are already indexed.")

    uploaded_files = st.file_uploader(
        "Files",
        type=["pdf", "csv", "txt", "md", "xlsx", "xls"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        for uploaded in uploaded_files:
            try:
                doc_id, facts = store_document(uploaded.name, uploaded.read())
                st.success(f"✅ {uploaded.name} indexed as document {doc_id}.")
                if facts:
                    st.caption(
                        f"🔍 Extracted **{len(facts)}** procurement fact(s)"
                    )
                    _render_facts_table(facts)
                else:
                    st.info("No structured procurement facts detected in this file.")
            except Exception as exc:
                st.error(f"{uploaded.name} could not be processed: {exc}")

    # --- Previously extracted facts from the database ---
    all_facts = get_procurement_facts()
    if all_facts:
        st.subheader("📊 All Extracted Procurement Facts")
        st.dataframe(
            [
                {
                    "Document": row["filename"],
                    "Field": row["field_name"],
                    "Value": row["field_value"],
                    "Confidence": row["confidence"].title() if row["confidence"] else "Medium",
                    "Extracted": row["extracted_at"],
                }
                for row in all_facts
            ],
            width="stretch",
            hide_index=True,
        )

    st.subheader("Indexed Documents")
    rows = list_documents()
    if rows:
        st.dataframe(
            [
                {
                    "Document ID": row["id"],
                    "Filename": row["filename"],
                    "Chunks": row["chunk_count"],
                    "Uploaded": row["uploaded_at"],
                }
                for row in rows
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("No documents indexed yet.")
