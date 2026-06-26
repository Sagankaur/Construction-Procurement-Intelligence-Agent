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

# Handle theme parameter and store in session state
if "theme" in query_params:
    st.session_state.theme = query_params["theme"]
elif "theme" not in st.session_state:
    st.session_state.theme = "light"

# Define theme colors based on current state
if st.session_state.theme == "dark":
    bg_color = "#081B33"       # Brand navy background
    text_color = "#F8FAFC"     # Off-white text
    card_bg = "#102B4C"        # Navy card background
    border_color = "#334155"   # Dark border
    navbar_bg = "#FFFFFF"      # Keep image logo clear
    navbar_text = "#94A3B8"    # Slate text for inactive links
    navbar_border = "#E5EAF2"  # Light navbar border
    shadow_color = "rgba(0, 0, 0, 0.25)"
    theme_emoji = "☀️"         # Show sun emoji to toggle to light mode
    next_theme = "light"
else:
    bg_color = BRAND_BG        # Clean SaaS background
    text_color = BRAND_NAVY    # Brand navy primary text
    card_bg = "#FFFFFF"        # White card background
    border_color = "#E5EAF2"   # Light thin border
    navbar_bg = "#FFFFFF"      # White navbar background
    navbar_text = BRAND_SLATE  # Grey text for inactive links
    navbar_border = "#E5EAF2"  # Light navbar border
    shadow_color = "rgba(0, 0, 0, 0.02)"
    theme_emoji = "🌙"         # Show moon emoji to toggle to dark mode
    next_theme = "dark"

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
    .stApp {{
        background-color: var(--bg-color) !important;
        color: var(--text-color);
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
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
     <a href="?page=Overview&theme={st.session_state.theme}" target="_self" style="text-decoration: none; color: {BRAND_ORANGE if selection == 'Overview' else navbar_text}; font-weight: {'700' if selection == 'Overview' else '500'}; font-size: 0.9rem; padding: 0.5rem 0.2rem; border-bottom: 2px solid {BRAND_ORANGE if selection == 'Overview' else 'transparent'}; transition: all 0.2s;">Overview</a>
     <a href="?page=Upload Documents&theme={st.session_state.theme}" target="_self" style="text-decoration: none; color: {BRAND_ORANGE if selection == 'Upload Documents' else navbar_text}; font-weight: {'700' if selection == 'Upload Documents' else '500'}; font-size: 0.9rem; padding: 0.5rem 0.2rem; border-bottom: 2px solid {BRAND_ORANGE if selection == 'Upload Documents' else 'transparent'}; transition: all 0.2; whitespace: nowrap;">Upload Documents</a>
     <a href="?page=Ask AI Agent&theme={st.session_state.theme}" target="_self" style="text-decoration: none; color: {BRAND_ORANGE if selection == 'Ask AI Agent' else navbar_text}; font-weight: {'700' if selection == 'Ask AI Agent' else '500'}; font-size: 0.9rem; padding: 0.5rem 0.2rem; border-bottom: 2px solid {BRAND_ORANGE if selection == 'Ask AI Agent' else 'transparent'}; transition: all 0.2; whitespace: nowrap;">Ask AI Agent</a>
     <a href="?page=Delay Prediction&theme={st.session_state.theme}" target="_self" style="text-decoration: none; color: {BRAND_ORANGE if selection == 'Delay Prediction' else navbar_text}; font-weight: {'700' if selection == 'Delay Prediction' else '500'}; font-size: 0.9rem; padding: 0.5rem 0.2rem; border-bottom: 2px solid {BRAND_ORANGE if selection == 'Delay Prediction' else 'transparent'}; transition: all 0.2; whitespace: nowrap;">Delay Prediction</a>
     <a href="?page=Vendor Risk&theme={st.session_state.theme}" target="_self" style="text-decoration: none; color: {BRAND_ORANGE if selection == 'Vendor Risk' else navbar_text}; font-weight: {'700' if selection == 'Vendor Risk' else '500'}; font-size: 0.9rem; padding: 0.5rem 0.2rem; border-bottom: 2px solid {BRAND_ORANGE if selection == 'Vendor Risk' else 'transparent'}; transition: all 0.2; whitespace: nowrap;">Vendor Risk</a>
     <a href="?page=Alerts&theme={st.session_state.theme}" target="_self" style="text-decoration: none; color: {BRAND_ORANGE if selection == 'Alerts' else navbar_text}; font-weight: {'700' if selection == 'Alerts' else '500'}; font-size: 0.9rem; padding: 0.5rem 0.2rem; border-bottom: 2px solid {BRAND_ORANGE if selection == 'Alerts' else 'transparent'}; transition: all 0.2;">Alerts</a>
  </div>
  <div style="display: flex; align-items: center; gap: 1rem;">
     <a href="?page={selection}&theme={next_theme}" target="_self" style="text-decoration: none; font-size: 1.1rem; cursor: pointer;">{theme_emoji}</a>
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
