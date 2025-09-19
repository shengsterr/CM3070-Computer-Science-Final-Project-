# app/ui_shared.py
from typing import List
from pathlib import Path
import streamlit as st

READ_MODE_IMG_WIDTH = 520  # smaller preview on Read page

def inject_css(font_px: int = 22, line_h: float = 1.6):
    st.set_page_config(page_title="Children's Storybook", page_icon="📚", layout="wide")
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800&display=swap');
    :root {{
      --story-font-size:{font_px}px; --story-line-height:{line_h};
      --accent:#7c3aed; --fg:#f8fafc;
    }}
    html, body, [class*="css"] {{ font-family:'Nunito', system-ui, -apple-system, Segoe UI, Roboto, sans-serif !important; }}

    .story-card {{ background:#0f172a; color:#e5e7eb; border:1px solid #1f2937; border-radius:18px; padding:20px 22px; }}
    .story-title {{ font-weight:800; font-size:calc(var(--story-font-size)+8px); margin:6px 0 12px; }}
    .story-paragraph {{ font-size:var(--story-font-size); line-height:var(--story-line-height); margin:8px 0; }}

    .page-card {{ background:transparent; padding:0; border-radius:0; box-shadow:none; }}
    .stImage img {{ border-radius:16px; display:block; }}

    .caption-box {{ background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.09);
                    border-radius:14px; padding:12px 14px; }}
    .caption {{ font-size:{max(16, font_px-2)}px; line-height:1.55; margin:0; }}

    .stButton>button {{
      background:linear-gradient(180deg, var(--accent), #6d28d9); border:0; color:var(--fg);
      border-radius:12px; padding:10px 14px; font-weight:700; box-shadow:0 6px 18px rgba(124,58,237,0.25);
    }}
    .stButton>button:hover {{ filter:brightness(1.08); }}

    .nav-row .stButton>button {{ background:#111827; border:1px solid #1f2937; color:#e5e7eb; box-shadow:none; }}
    .nav-row .stButton>button:hover {{ background:#0b1220; }}

    .pill {{ display:inline-block; padding:4px 10px; border-radius:999px; background:#eef2ff; color:#3730a3;
             font-size:12px; font-weight:700; margin-right:8px; }}
    .stProgress > div > div {{ background:transparent !important; }}
    </style>
    """, unsafe_allow_html=True)

def split_paragraphs(text: str) -> List[str]:
    return [p.strip() for p in (text or "").split("\n\n") if p.strip()]

def init_state():
    ss = st.session_state
    ss.setdefault("story", "")
    ss.setdefault("image_path", None)
    ss.setdefault("title", "My Storybook")
    ss.setdefault("scenes", [])      # list of {"caption","image_path"}
    ss.setdefault("page_idx", 0)     # for preview nav
    Path("data/pdfs").mkdir(parents=True, exist_ok=True)
    Path("data/images").mkdir(parents=True, exist_ok=True)
    Path("data/audio").mkdir(parents=True, exist_ok=True)
    return ss

def top_nav(active: str):
    cols = st.columns([1,1,1,1,4])
    with cols[0]:
        st.page_link("Home.py", label="🏠 Home")
    with cols[1]:
        st.page_link("pages/1_Create_Story.py", label="✏️ Create")
    with cols[2]:
        st.page_link("pages/2_Read_Story.py", label="📖 Read")
    with cols[3]:
        st.page_link("pages/3_Library.py", label="🗂️ Library")
