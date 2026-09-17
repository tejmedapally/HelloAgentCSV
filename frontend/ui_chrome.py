"""Shared visual chrome for the Grounded FAQ Streamlit UI."""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

_HEADER_IMAGE = Path(__file__).resolve().parent / "static" / "hello-agent-header.png"
_FONT = "Arial, Helvetica, sans-serif"
_ICON = '"Material Symbols Rounded"'

# Keep CSS injection out of normal document flow (st.html otherwise leaves huge gaps).
_STYLES = f"""
<style>
/* Hide style-only st.html / markdown hosts so they take no vertical space */
div[data-testid="stElementContainer"]:has(> div[data-testid="stHtml"] > style),
div[data-testid="stElementContainer"]:has(> div[data-testid="stMarkdownContainer"] > style),
div[data-testid="stHtml"]:has(> style) {{
  height: 0 !important;
  min-height: 0 !important;
  max-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
  border: none !important;
  position: absolute !important;
  left: -9999px !important;
  opacity: 0 !important;
  pointer-events: none !important;
}}

/* Compact Streamlit element spacing */
[data-testid="stMain"] [data-testid="stVerticalBlock"] {{
  gap: 0.4rem !important;
}}
[data-testid="stMain"] [data-testid="stHorizontalBlock"] {{
  gap: 0.75rem !important;
  align-items: stretch !important;
}}
/* Equal-height Upload / Ask / Answer bordered panels */
[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
  display: flex !important;
  flex-direction: column !important;
  align-self: stretch !important;
}}
[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div,
[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div {{
  flex: 1 1 auto !important;
  height: 100% !important;
}}
[data-testid="stHorizontalBlock"] [data-testid="stVerticalBlockBorderWrapper"] {{
  flex: 1 1 auto !important;
  height: 100% !important;
  min-height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
}}
[data-testid="stHorizontalBlock"] [data-testid="stVerticalBlockBorderWrapper"] > div {{
  flex: 1 1 auto !important;
  height: 100% !important;
}}
div[data-testid="stElementContainer"] {{
  margin-bottom: 0 !important;
}}

.stApp, body {{
  font-family: {_FONT};
  color: #0F3A44;
}}
/* Only target text leaves — never wrapping containers (breaks Material icons) */
h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label,
[data-testid="stCaptionContainer"] p,
div.stButton > button,
div.stFormSubmitButton > button,
.stTextInput input,
.stTextArea textarea {{
  font-family: {_FONT} !important;
}}

/* Icons must keep ligature font (Streamlit default) */
[data-testid="stIconMaterial"],
span[data-testid="stIconMaterial"] {{
  font-family: {_ICON} !important;
  font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 24 !important;
  -webkit-text-fill-color: unset !important;
  opacity: unset !important;
}}

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section.main {{
  background-color: #E5F0F2 !important;
}}
[data-testid="stHeader"] {{
  background: transparent !important;
}}
.block-container {{
  max-width: 100% !important;
  width: 100% !important;
  padding-top: 0.4rem !important;
  padding-bottom: 4.5rem !important;
  padding-left: 1.25rem !important;
  padding-right: 1.25rem !important;
}}

[data-testid="stFileUploader"] {{
  margin: 0 !important;
  padding: 0 !important;
}}
[data-testid="stFileUploaderDropzone"] {{
  background: #F7FBFC !important;
  border: 1px dashed #1F6F7C !important;
  border-radius: 0.65rem !important;
  padding: 0.85rem 1rem !important;
}}

div.stButton > button,
div.stFormSubmitButton > button {{
  border-radius: 0.55rem !important;
  font-weight: 700 !important;
  min-height: 2.45rem !important;
  font-size: 1rem !important;
}}
div.stButton > button[kind="primary"],
div.stFormSubmitButton > button {{
  background-color: #0E5C6B !important;
  background-image: none !important;
  border: 2px solid #0A4550 !important;
  color: #FFFFFF !important;
}}
div.stButton > button[kind="secondary"],
div.stButton > button:not([kind="primary"]) {{
  background-color: #FFFFFF !important;
  border: 2px solid #1F6F7C !important;
  color: #0F3A44 !important;
}}
div.stButton > button:disabled {{
  background-color: #C5D5D9 !important;
  border-color: #9BB0B6 !important;
  color: #3D555C !important;
}}

.stTextInput input, .stTextArea textarea {{
  border-radius: 0.5rem !important;
  background-color: #FFFFFF !important;
  color: #0F3A44 !important;
}}

#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
</style>
"""


def inject_styles() -> None:
    """Inject CSS once; host element is collapsed by the CSS itself."""
    st.html(_STYLES)


def section_header(title: str) -> None:
    """Compact section title (no extra outer margins)."""
    st.html(
        f'<div style="font-family:{_FONT};font-size:1.15rem;font-weight:700;'
        "color:#0F3A44;margin:0;padding:0.4rem 0.65rem;background:#D5E8EC;"
        'border-left:5px solid #0E5C6B;border-radius:0.35rem;">'
        f"{title}</div>"
    )


def _header_image_data_uri() -> str | None:
    if not _HEADER_IMAGE.is_file():
        return None
    encoded = base64.b64encode(_HEADER_IMAGE.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_header(
    *,
    tagline: str = "Answers only from your uploaded CSVs — never from general knowledge.",
) -> None:
    """Full-width branded header banner."""
    img_uri = _header_image_data_uri()
    img_html = (
        f'<img src="{img_uri}" alt="" '
        'style="width:88px;height:88px;border-radius:0.65rem;object-fit:cover;'
        'border:1px solid rgba(255,255,255,0.18);flex:0 0 auto;" />'
        if img_uri
        else ""
    )
    st.html(
        f"""
<div style="
  width:100%;box-sizing:border-box;margin:0 0 0.65rem 0;padding:1rem 1.2rem;
  border-radius:0.85rem;
  background:linear-gradient(135deg,#0B2B33 0%,#0E4A56 55%,#0E748A 120%);
  color:#F4F7F8;box-shadow:0 8px 20px rgba(11,43,51,0.18);
  display:flex;align-items:center;gap:1rem;font-family:{_FONT};
">
  {img_html}
  <div style="flex:1;min-width:0;font-family:{_FONT};">
    <p style="margin:0 0 0.2rem 0;font-size:0.7rem;letter-spacing:0.14em;
      text-transform:uppercase;font-weight:700;opacity:0.88;font-family:{_FONT};">
      CSV FAQ agent</p>
    <h1 style="margin:0 0 0.3rem 0;font-family:{_FONT};
      font-size:clamp(1.7rem,3.2vw,2.3rem);font-weight:700;line-height:1.1;
      color:#FFFFFF;">Grounded FAQ</h1>
    <p style="margin:0;font-size:0.98rem;opacity:0.92;max-width:42rem;line-height:1.35;
      font-family:{_FONT};">{tagline}</p>
  </div>
</div>
"""
    )


def render_footer() -> None:
    """Full-width footer pinned to the bottom of the viewport."""
    st.html(
        f"""
<div style="
  position:fixed;left:0;right:0;bottom:0;z-index:99999;width:100%;
  box-sizing:border-box;padding:0.75rem 1.5rem;background:#0B2B33;
  color:rgba(244,247,248,0.9);font-size:0.88rem;display:flex;
  justify-content:space-between;align-items:center;gap:0.75rem;
  font-family:{_FONT};
">
  <strong style="font-family:{_FONT};font-weight:700;color:#FFFFFF;font-size:1rem;">
    Grounded FAQ</strong>
  <span style="font-family:{_FONT};">
    Data-only answers · Claude on the backend · Week 0
  </span>
</div>
"""
    )
