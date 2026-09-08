"""
Official Kayfa Academy Design System & Theme Engine.
Strictly inspired by Kayfa Academy:
- Blue background (#3750EB) with Pure White text (#FFFFFF) on all buttons & active items.
- Deep Indigo (#1E2B68) for secondary badges.
- Crisp Light canvas (#F8FAFD), Zero black boxes.
"""
import os
import base64
import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _find_kayfa_svg() -> str:
    candidates = ["kayfa.svg", "Kayfa.svg", "KAYFA.svg"]
    for name in candidates:
        p = os.path.join(ROOT_DIR, name)
        if os.path.exists(p):
            return p
    return ""

def get_kayfa_logo_html(width: int = 180) -> str:
    svg_path = _find_kayfa_svg()
    if svg_path and os.path.exists(svg_path):
        try:
            with open(svg_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                return f'<img src="data:image/svg+xml;base64,{encoded}" width="{width}" alt="Kayfa Logo" style="display:inline-block; vertical-align:middle;" />'
        except Exception:
            pass
            
    return f'''
    <div style="display:inline-flex; align-items:center; gap:8px;">
        <span style="font-size:26px; font-weight:900; color:#3750EB; font-family:'Cairo', sans-serif;">كَيْفَ</span>
        <span style="font-size:12px; font-weight:800; color:#1E2B68; letter-spacing:1.5px;">ACADEMY</span>
    </div>
    '''

KAYFA_SVG_LOGO = get_kayfa_logo_html(180)

def apply_kayfa_theme(is_arabic: bool = False):
    direction = "rtl" if is_arabic else "ltr"
    align = "right" if is_arabic else "left"
    
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        
        /* 1. NO BLACK HEADER OR BLACK BARS ANYWHERE */
        header[data-testid="stHeader"] {{
            background-color: #FFFFFF !important;
            border-bottom: 1px solid #E8EEF5 !important;
        }}
        header[data-testid="stHeader"] * {{
            color: #1E2B68 !important;
        }}
        
        .stApp, [data-testid="stAppViewContainer"], .main {{
            background-color: #F8FAFD !important;
            color: #1A2552 !important;
            font-family: {'Cairo' if is_arabic else "'Plus Jakarta Sans'"}, -apple-system, sans-serif !important;
            direction: {direction};
            text-align: {align};
        }}
        
        /* 2. SIDEBAR: CRISP WHITE, NO BLACK CONTAINERS */
        [data-testid="stSidebar"] {{
            background-color: #FFFFFF !important;
            border-right: 1px solid #E8EEF5 !important;
        }}
        
        /* 3. ALL BUTTONS: ROYAL BLUE BACKGROUND WITH CRISP WHITE TEXT (NEVER BLACK) */
        button, 
        .stButton > button, 
        button[kind="primary"], 
        button[kind="secondary"], 
        .stFormSubmitButton > button,
        [data-testid="baseButton-secondary"],
        [data-testid="baseButton-primary"] {{
            background-color: #3750EB !important;
            background-image: none !important;
            border: 1.5px solid #3750EB !important;
            color: #FFFFFF !important;
            border-radius: 9999px !important; /* Kayfa Pill buttons */
            font-weight: 700 !important;
            font-size: 0.92rem !important;
            padding: 0.6rem 1.4rem !important;
            box-shadow: 0 4px 14px rgba(55, 80, 235, 0.25) !important;
            transition: all 0.2s ease !important;
        }}
        
        /* Force child spans and paragraphs inside buttons to be PURE WHITE */
        button *, 
        .stButton > button *, 
        button[kind="secondary"] *,
        button[kind="primary"] * {{
            color: #FFFFFF !important;
            fill: #FFFFFF !important;
        }}
        
        button:hover, 
        .stButton > button:hover,
        button[kind="secondary"]:hover {{
            background-color: #2638C4 !important;
            border-color: #2638C4 !important;
            box-shadow: 0 6px 18px rgba(55, 80, 235, 0.35) !important;
        }}

        /* 4. SIDEBAR NAVIGATION: KAYFA PILL BUTTONS (BLUE BG + WHITE TEXT) */
        .kayfa-nav-active button {{
            background-color: #3750EB !important;
            border-color: #3750EB !important;
            color: #FFFFFF !important;
            border-radius: 9999px !important;
            font-weight: 800 !important;
            box-shadow: 0 4px 14px rgba(55, 80, 235, 0.35) !important;
        }}
        .kayfa-nav-active button * {{
            color: #FFFFFF !important;
        }}
        
        .kayfa-nav-idle button {{
            background-color: #EDF2FE !important;
            border: 1px solid #C7D7FD !important;
            color: #1E2B68 !important;
            border-radius: 9999px !important;
            font-weight: 700 !important;
            box-shadow: none !important;
        }}
        .kayfa-nav-idle button * {{
            color: #1E2B68 !important;
        }}
        .kayfa-nav-idle button:hover {{
            background-color: #3750EB !important;
            border-color: #3750EB !important;
            color: #FFFFFF !important;
        }}
        .kayfa-nav-idle button:hover * {{
            color: #FFFFFF !important;
        }}
        
        /* 5. NO BLACK BOXES FOR TABLES OR DATA */
        [data-testid="stDataFrame"], [data-testid="stTable"], .element-container div:empty {{
            background: #FFFFFF !important;
            color: #1A2552 !important;
            border-radius: 12px !important;
        }}
        
        /* 6. FIX BOTTOM CHAT INPUT (REMOVE UGLY BLACK BOTTOM BAR) */
        [data-testid="stChatInput"], [data-testid="stChatInputContainer"], [data-testid="stBottom"] {{
            background-color: #FFFFFF !important;
            border-top: 1px solid #E8EEF5 !important;
        }}
        [data-testid="stBottom"] > div {{
            background-color: #FFFFFF !important;
        }}
        [data-testid="stChatInput"] textarea {{
            background-color: #F8FAFD !important;
            color: #1A2552 !important;
            border: 1.5px solid #CBD5E1 !important;
            border-radius: 9999px !important;
            padding: 0.75rem 1.25rem !important;
        }}
        [data-testid="stChatInput"] button {{
            background: #3750EB !important;
            border-radius: 50% !important;
            color: #FFFFFF !important;
        }}
        
        /* 7. CARDS & SECTIONS */
        .kayfa-card {{
            background: #FFFFFF !important;
            border: 1px solid #E8EEF5 !important;
            border-radius: 16px !important;
            padding: 1.5rem !important;
            margin-bottom: 1.25rem !important;
            box-shadow: 0 4px 16px rgba(30, 43, 104, 0.04) !important;
        }}
        
        .kpi-title {{
            font-size: 0.78rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748B !important;
        }}
        
        .kpi-value {{
            font-size: 2.2rem;
            font-weight: 900;
            color: #1E2B68 !important;
            line-height: 1.1;
            margin-top: 0.25rem;
        }}
        
        /* 8. KAYFA BADGES & PILLS */
        .kayfa-pill-blue {{
            background-color: #3750EB;
            color: #FFFFFF !important;
            padding: 0.4rem 1.2rem;
            border-radius: 9999px;
            font-size: 0.82rem;
            font-weight: 700;
            display: inline-block;
        }}
        
        .kayfa-pill-indigo {{
            background-color: #1E2B68;
            color: #FFFFFF !important;
            padding: 0.4rem 1.2rem;
            border-radius: 9999px;
            font-size: 0.82rem;
            font-weight: 700;
            display: inline-block;
        }}
        
        .kayfa-pill-outline {{
            background-color: #FFFFFF;
            color: #3750EB !important;
            border: 2px solid #3750EB;
            padding: 0.35rem 1.1rem;
            border-radius: 9999px;
            font-size: 0.82rem;
            font-weight: 700;
            display: inline-block;
        }}
    </style>
    """, unsafe_allow_html=True)

apply_enterprise_theme = apply_kayfa_theme