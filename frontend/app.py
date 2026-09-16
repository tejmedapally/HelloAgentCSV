"""Hello Agent — minimal Streamlit shell (connection + session)."""

from __future__ import annotations

import streamlit as st
from httpx import HTTPError

from api_client import BackendClient

st.set_page_config(page_title="Hello Agent", page_icon="📄", layout="centered")
st.title("Hello Agent")
st.caption("CSV FAQ assistant — backend connection check")


def _get_client() -> BackendClient:
    if "backend_client" not in st.session_state:
        st.session_state.backend_client = BackendClient()
    return st.session_state.backend_client


client = _get_client()

st.subheader("Backend connection")
st.write(f"**BACKEND_URL:** `{client.base_url}`")

col1, col2 = st.columns(2)

with col1:
    if st.button("Check health", use_container_width=True):
        try:
            payload = client.health()
            st.session_state.health_ok = True
            st.session_state.health_detail = payload
            st.session_state.health_error = None
        except (HTTPError, OSError) as exc:
            st.session_state.health_ok = False
            st.session_state.health_detail = None
            st.session_state.health_error = str(exc)

with col2:
    if st.button("Create session", use_container_width=True):
        try:
            data = client.create_session()
            st.session_state.session_id = data["id"]
            st.session_state.session_error = None
        except (HTTPError, OSError) as exc:
            st.session_state.session_error = str(exc)

if st.session_state.get("health_ok") is True:
    st.success(f"Backend healthy: `{st.session_state.health_detail}`")
elif st.session_state.get("health_ok") is False:
    st.error(f"Backend unreachable: {st.session_state.health_error}")

st.subheader("Session")
session_id = st.session_state.get("session_id")
if session_id:
    st.info(f"Session ID: `{session_id}`")
    if st.button("Refresh session from backend"):
        try:
            summary = client.get_session(session_id)
            st.session_state.session_summary = summary
            st.session_state.session_error = None
        except (HTTPError, OSError, ValueError) as exc:
            st.session_state.session_error = str(exc)
    if st.session_state.get("session_summary"):
        st.json(st.session_state.session_summary)
else:
    st.write("No session yet. Click **Create session** after the backend is running.")

if st.session_state.get("session_error"):
    st.error(st.session_state.session_error)

st.divider()
st.caption("Upload / ask UI comes in later tasks. Start the API with: `uv run uvicorn app.main:app --reload --port 8000` from `backend/`.")
