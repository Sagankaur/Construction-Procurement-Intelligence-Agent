import streamlit as st

from src.database import list_documents
from src.document_loader import seed_sample_documents, store_document


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
                doc_id = store_document(uploaded.name, uploaded.read())
                st.success(f"{uploaded.name} indexed as document {doc_id}.")
            except Exception as exc:
                st.error(f"{uploaded.name} could not be processed: {exc}")

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
