import importlib.util
from pathlib import Path

import streamlit as st

from src.database import init_db

BASE_DIR = Path(__file__).resolve().parent

init_db()

st.set_page_config(
    page_title="SiteSage AI",
    page_icon="SS",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --sage-ink: #17202a;
        --sage-panel: #ffffff;
        --sage-muted: #64748b;
        --sage-line: #d8dee7;
        --sage-accent: #0f766e;
        --sage-warn: #b45309;
        --sage-danger: #b91c1c;
    }
    .stApp {
        background: #f5f7fa;
        color: var(--sage-ink);
    }
    section[data-testid="stSidebar"] {
        background: #ecf1f5;
        border-right: 1px solid var(--sage-line);
    }
    /* Hide Streamlit default native navigation */
    div[data-testid="stSidebarNav"] {
        display: none !important;
    }
    .stButton > button {
        border-radius: 6px;
        border: 1px solid #0f766e;
        color: #ffffff;
        background: #0f766e;
        min-height: 2.35rem;
    }
    .stButton > button:hover {
        border-color: #115e59;
        background: #115e59;
        color: #ffffff;
    }
    div[data-testid="stMetric"] {
        background: var(--sage-panel);
        border: 1px solid var(--sage-line);
        border-radius: 8px;
        padding: 0.85rem 1rem;
    }
    h1, h2, h3 {
        letter-spacing: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

PAGES = {
    "Overview": "pages/01_Overview.py",
    "Upload Documents": "pages/02_Upload_Documents.py",
    "Ask AI Agent": "pages/03_Ask_AI_Agent.py",
    "Delay Prediction": "pages/04_Delay_Prediction.py",
    "Vendor Risk": "pages/05_Vendor_Risk.py",
    "Alerts": "pages/06_Alerts.py",
}

st.sidebar.title("SiteSage AI")
selection = st.sidebar.radio("Navigate", list(PAGES.keys()))
st.sidebar.caption("Construction Procurement Intelligence")

page_path = BASE_DIR / PAGES[selection]
module_name = page_path.stem
spec = importlib.util.spec_from_file_location(module_name, page_path)
if spec is None or spec.loader is None:
    st.error(f"Could not load page: {selection}")
else:
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()
