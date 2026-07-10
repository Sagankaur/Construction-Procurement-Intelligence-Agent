import base64
import importlib.util
from pathlib import Path

import streamlit as st

from src.database import init_db

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "logo.jpeg"
WORDMARK_PATH = BASE_DIR / "name.jpeg"

BRAND_NAVY = "#07315F"
BRAND_ORANGE = "#FF7A18"
BRAND_SLATE = "#5E6673"
BRAND_BG = "#F7F9FC"


def image_data_uri(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    mime = "jpeg" if suffix in {"jpg", "jpeg"} else suffix
    image_data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/{mime};base64,{image_data}"

init_db()

st.set_page_config(
    page_title="SiteSage AI",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "SS",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Navigation configuration
# ---------------------------------------------------------------------------
PAGES = {
    "Overview": "pages/01_Overview.py",
    "Upload Documents": "pages/02_Upload_Documents.py",
    "Ask AI Agent": "pages/03_Ask_AI_Agent.py",
    "Delay Prediction": "pages/04_Delay_Prediction.py",
    "Vendor Risk": "pages/05_Vendor_Risk.py",
    "Alerts": "pages/06_Alerts.py",
}

# Handle query parameters for routing
query_params = st.query_params
if "page" in query_params:
    selection = query_params["page"]
    if selection not in PAGES:
        selection = "Overview"
else:
    selection = "Overview"

# Set theme strictly to light mode (day theme)
st.session_state.theme = "light"

bg_color = BRAND_BG        # Clean SaaS background
text_color = BRAND_NAVY    # Brand navy primary text
card_bg = "#FFFFFF"        # White card background
border_color = "#E5EAF2"   # Light thin border
navbar_bg = "#FFFFFF"      # White navbar background
navbar_text = BRAND_SLATE  # Grey text for inactive links
navbar_border = "#E5EAF2"  # Light navbar border
shadow_color = "rgba(0, 0, 0, 0.02)"

# ---------------------------------------------------------------------------
# Global Design & Navbar Styling
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    :root {{
        --primary-navy: {'#FFFFFF' if st.session_state.theme == 'dark' else BRAND_NAVY};
        --primary-blue: {BRAND_ORANGE};
        --success: #10B981;
        --warning: {BRAND_ORANGE};
        --critical: #EF4444;
        --text-color: {text_color};
        --bg-color: {bg_color};
        --card-bg: {card_bg};
        --border-color: {border_color};
    }}

    /* Global Body and Font Settings */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"], [data-testid="stAppViewBlockContainer"] > div {{
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    /* Force all child paragraphs, spans, labels, and markdown to respect text color */
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span, .stText, p, li, label, div[data-testid="stMarkdownContainer"] p {{
        color: var(--text-color) !important;
    }}

    /* Streamlit metrics text styling */
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] * {{
        color: var(--text-color) !important;
    }}
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {{
        color: var(--text-color) !important;
    }}

    /* Widget Labels (selectbox, inputs, etc.) */
    label[data-testid="stWidgetLabel"] p, label[data-testid="stWidgetLabel"] span {{
        color: var(--text-color) !important;
    }}

    /* Streamlit tabs text styling */
    button[data-baseweb="tab"] > div, button[data-baseweb="tab"] * {{
        color: var(--text-color) !important;
    }}

    /* Hide Streamlit default native navigation and sidebar */
    [data-testid="stSidebar"] {{
        display: none !important;
    }}
    [data-testid="stHeader"] {{
        display: none !important;
    }}

    /* Main App View container padding-top to account for fixed header */
    div[data-testid="stAppViewBlockContainer"] {{
        padding-top: 6.8rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1240px !important;
        margin: 0 auto !important;
    }}

    /* Premium Button Styles */
    .stButton > button {{
        border-radius: 8px;
        border: 1px solid var(--primary-blue);
        color: #FFFFFF !important;
        background: var(--primary-blue);
        font-weight: 600;
        letter-spacing: -0.01em;
        padding: 0.6rem 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: all 0.2s ease-in-out;
        width: 100%;
    }}
    .stButton > button:hover {{
        background: {BRAND_NAVY};
        border-color: {BRAND_NAVY};
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}

    /* Premium Hover & Elevation Effects for Cards & Banners */
    .stat-card, .fact-card, .vendor-card, .exec-summary-card, .recom-card, .recom-box, .trend-insight-box-new, .alert-box, .source-card {{
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }}
    .stat-card:hover, .fact-card:hover, .vendor-card:hover, .exec-summary-card:hover, .recom-card:hover, .recom-box:hover, .trend-insight-box-new:hover, .alert-box:hover, .source-card:hover {{
        transform: translateY(-4px) !important;
        box-shadow: 0 12px 24px rgba(7, 49, 95, 0.08) !important;
        border-color: {BRAND_ORANGE} !important;
    }}
    
    /* Navigation Link Hover & Transition effects */
    div a[target="_self"] {{
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }}
    div a[target="_self"]:hover {{
        color: {BRAND_ORANGE} !important;
        opacity: 1 !important;
        border-bottom-color: {BRAND_ORANGE} !important;
        transform: translateY(-1px) !important;
    }}

    /* Typography Hierarchy styling */
    h1, h2, h3, h4, h5, h6 {{
        font-weight: 700 !important;
        letter-spacing: -0.03em !important;
        color: var(--primary-navy) !important;
    }}
    h1 {{ font-size: 2rem !important; margin-bottom: 0.5rem !important; }}
    h2 {{ font-size: 1.5rem !important; margin-top: 1rem !important; margin-bottom: 0.75rem !important; }}
    h3 {{ font-size: 1.2rem !important; }}

    /* Custom scrollbars */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: #F1F5F9;
    }}
    ::-webkit-scrollbar-thumb {{
        background: #CBD5E1;
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: #94A3B8;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Custom Top Navigation Bar HTML
# ---------------------------------------------------------------------------
if LOGO_PATH.exists() and WORDMARK_PATH.exists():
    logo_html = (
        f'<img src="{image_data_uri(LOGO_PATH)}" alt="SiteSage AI mark" '
        'style="width: 38px; height: 38px; object-fit: contain; flex-shrink: 0;" />'
        f'<img src="{image_data_uri(WORDMARK_PATH)}" alt="SiteSage AI" '
        'style="width: 170px; height: 32px; object-fit: contain; object-position: left center; flex-shrink: 0;" />'
    )
elif LOGO_PATH.exists():
    logo_html = (
        f'<img src="{image_data_uri(LOGO_PATH)}" alt="SiteSage AI logo" '
        'style="width: 42px; height: 42px; object-fit: contain; flex-shrink: 0;" />'
    )
else:
    logo_html = (
        f'<svg width="22" height="22" viewBox="0 0 24 24" fill="{BRAND_ORANGE}" '
        'style="flex-shrink: 0;"><path d="M12 2L14.8 9.2L22 12L14.8 14.8L12 22L9.2 14.8L2 12L9.2 9.2Z"/></svg>'
    )

navbar_html = f"""
<div style="
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: {navbar_bg};
    border-bottom: 1px solid {navbar_border};
    padding: 0.75rem 2rem;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 999999;
    height: 60px;
    box-sizing: border-box;
    font-family: 'Plus Jakarta Sans', sans-serif;
    box-shadow: 0 1px 3px {shadow_color};
">
  <div style="display: flex; align-items: center; gap: 0.65rem; width: 230px; min-width: 230px;">
     {logo_html}
  </div>
  <div style="display: flex; gap: 1.5rem; height: 100%; align-items: center;">
     <a href="?page=Overview" target="_self" style="text-decoration: none; color: {BRAND_ORANGE if selection == 'Overview' else navbar_text}; font-weight: {'700' if selection == 'Overview' else '500'}; font-size: 0.9rem; padding: 0.5rem 0.2rem; border-bottom: 2px solid {BRAND_ORANGE if selection == 'Overview' else 'transparent'}; transition: all 0.2s;">Overview</a>
     <a href="?page=Upload Documents" target="_self" style="text-decoration: none; color: {BRAND_ORANGE if selection == 'Upload Documents' else navbar_text}; font-weight: {'700' if selection == 'Upload Documents' else '500'}; font-size: 0.9rem; padding: 0.5rem 0.2rem; border-bottom: 2px solid {BRAND_ORANGE if selection == 'Upload Documents' else 'transparent'}; transition: all 0.2; whitespace: nowrap;">Upload Documents</a>
     <a href="?page=Ask AI Agent" target="_self" style="text-decoration: none; color: {BRAND_ORANGE if selection == 'Ask AI Agent' else navbar_text}; font-weight: {'700' if selection == 'Ask AI Agent' else '500'}; font-size: 0.9rem; padding: 0.5rem 0.2rem; border-bottom: 2px solid {BRAND_ORANGE if selection == 'Ask AI Agent' else 'transparent'}; transition: all 0.2; whitespace: nowrap;">Ask AI Agent</a>
     <a href="?page=Delay Prediction" target="_self" style="text-decoration: none; color: {BRAND_ORANGE if selection == 'Delay Prediction' else navbar_text}; font-weight: {'700' if selection == 'Delay Prediction' else '500'}; font-size: 0.9rem; padding: 0.5rem 0.2rem; border-bottom: 2px solid {BRAND_ORANGE if selection == 'Delay Prediction' else 'transparent'}; transition: all 0.2; whitespace: nowrap;">Delay Prediction</a>
     <a href="?page=Vendor Risk" target="_self" style="text-decoration: none; color: {BRAND_ORANGE if selection == 'Vendor Risk' else navbar_text}; font-weight: {'700' if selection == 'Vendor Risk' else '500'}; font-size: 0.9rem; padding: 0.5rem 0.2rem; border-bottom: 2px solid {BRAND_ORANGE if selection == 'Vendor Risk' else 'transparent'}; transition: all 0.2; whitespace: nowrap;">Vendor Risk</a>
     <a href="?page=Alerts" target="_self" style="text-decoration: none; color: {BRAND_ORANGE if selection == 'Alerts' else navbar_text}; font-weight: {'700' if selection == 'Alerts' else '500'}; font-size: 0.9rem; padding: 0.5rem 0.2rem; border-bottom: 2px solid {BRAND_ORANGE if selection == 'Alerts' else 'transparent'}; transition: all 0.2;">Alerts</a>
  </div>
  <div style="display: flex; align-items: center; gap: 1rem; width: 230px; min-width: 230px; justify-content: flex-end;">
  </div>
</div>
"""
st.markdown(navbar_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Module Loading & Page Execution
# ---------------------------------------------------------------------------
page_path = BASE_DIR / PAGES[selection]
module_name = page_path.stem
spec = importlib.util.spec_from_file_location(module_name, page_path)
if spec is None or spec.loader is None:
    st.error(f"Could not load page: {selection}")
else:
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()
