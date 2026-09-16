"""Hello Agent — Streamlit UI for CSV upload and FAQ ask."""

from __future__ import annotations

import streamlit as st
from httpx import HTTPError, HTTPStatusError

from api_client import BackendClient

st.set_page_config(page_title="Hello Agent", page_icon="📄", layout="centered")
st.title("Hello Agent")
st.caption("Upload CSVs and ask questions grounded in your data")


def _get_client() -> BackendClient:
    if "backend_client" not in st.session_state:
        # Ask calls Claude; allow longer than the default 30s.
        st.session_state.backend_client = BackendClient(timeout=120.0)
    return st.session_state.backend_client


def _error_detail(exc: BaseException) -> str:
    if isinstance(exc, HTTPStatusError) and exc.response is not None:
        try:
            payload = exc.response.json()
            detail = payload.get("detail")
            if detail:
                return str(detail)
        except ValueError:
            pass
        return f"HTTP {exc.response.status_code}: {exc.response.text}"
    return str(exc)


def _ensure_session(client: BackendClient) -> str:
    sid = st.session_state.get("session_id") or client.session_id
    if sid:
        client.session_id = sid
        st.session_state.session_id = sid
        return sid
    data = client.create_session()
    sid = str(data["id"])
    st.session_state.session_id = sid
    return sid


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
            st.session_state.health_error = _error_detail(exc)

with col2:
    if st.button("Create session", use_container_width=True):
        try:
            data = client.create_session()
            st.session_state.session_id = data["id"]
            st.session_state.session_error = None
            st.session_state.sources = data.get("sources", [])
        except (HTTPError, OSError) as exc:
            st.session_state.session_error = _error_detail(exc)

if st.session_state.get("health_ok") is True:
    st.success(f"Backend healthy: `{st.session_state.health_detail}`")
elif st.session_state.get("health_ok") is False:
    st.error(f"Backend unreachable: {st.session_state.health_error}")

st.subheader("Session")
session_id = st.session_state.get("session_id")
if session_id:
    st.info(f"Session ID: `{session_id}`")
else:
    st.write("No session yet — one will be created automatically on upload.")

if st.session_state.get("session_error"):
    st.error(st.session_state.session_error)

st.divider()
st.subheader("Upload CSVs")
uploads = st.file_uploader(
    "Choose one or more CSV files",
    type=["csv"],
    accept_multiple_files=True,
)

if st.button("Upload to session", type="primary", disabled=not uploads):
    try:
        _ensure_session(client)
        files = [(f.name, f.getvalue()) for f in uploads]
        result = client.upload_sources(files)
        sources = result.get("sources", [])
        st.session_state.sources = sources
        st.session_state.session_summary = {"id": client.session_id, "sources": sources}
        st.session_state.upload_error = None
        st.session_state.answer = None
        st.success(f"Uploaded {len(sources)} source(s).")
    except (HTTPError, OSError, ValueError) as exc:
        st.session_state.upload_error = _error_detail(exc)

if st.session_state.get("upload_error"):
    st.error(st.session_state.upload_error)

sources = st.session_state.get("sources") or []
if sources:
    st.write("**Active sources**")
    for src in sources:
        st.write(
            f"- `{src.get('filename')}` — {src.get('row_count', '?')} rows, "
            f"columns: {', '.join(src.get('columns') or [])}"
        )

st.divider()
st.subheader("Ask a question")
question = st.text_area(
    "Question",
    placeholder="e.g. What is the shipping time?",
    height=100,
)
ask_disabled = not question.strip() or not sources

if ask_disabled and question.strip() and not sources:
    st.warning("Upload at least one CSV before asking.")

if st.button("Ask", type="primary", disabled=ask_disabled):
    try:
        _ensure_session(client)
        with st.spinner("Asking the agent…"):
            answer = client.ask(question)
        st.session_state.answer = answer
        st.session_state.ask_error = None
    except (HTTPError, OSError, ValueError) as exc:
        st.session_state.ask_error = _error_detail(exc)
        st.session_state.answer = None

if st.session_state.get("ask_error"):
    st.error(st.session_state.ask_error)

answer = st.session_state.get("answer")
if answer:
    status = answer.get("status", "")
    if status == "ok":
        st.success("Answer")
    elif status == "not_found":
        st.warning("Not found in uploaded data")
    else:
        st.error("Error from agent")
    # text_area makes copy-to-clipboard straightforward in the browser
    st.text_area(
        "Answer text",
        value=answer.get("text", ""),
        height=160,
        disabled=True,
        label_visibility="collapsed",
    )
    filenames = answer.get("source_filenames") or []
    if filenames:
        st.caption("Sources: " + ", ".join(filenames))

st.divider()
st.caption(
    "Start the API with: `uv run uvicorn app.main:app --reload --port 8000` from `backend/`."
)
