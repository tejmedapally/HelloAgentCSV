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


def _set_sources(sources: list) -> None:
    st.session_state.sources = sources
    st.session_state.session_summary = {
        "id": st.session_state.get("session_id"),
        "sources": sources,
    }


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
            _set_sources(data.get("sources", []))
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
    refresh_col, clear_col = st.columns(2)
    with refresh_col:
        if st.button("Refresh sources", use_container_width=True):
            try:
                listed = client.list_sources(session_id)
                _set_sources(listed.get("sources", []))
                st.session_state.session_error = None
            except (HTTPError, OSError, ValueError) as exc:
                st.session_state.session_error = _error_detail(exc)
    with clear_col:
        if st.button("Clear all sources", use_container_width=True):
            try:
                client.clear_sources(session_id)
                _set_sources([])
                st.session_state.answer = None
                st.session_state.upload_error = None
                st.session_state.upload_warnings = None
                st.session_state.session_error = None
                st.success("All sources cleared.")
            except (HTTPError, OSError, ValueError) as exc:
                st.session_state.session_error = _error_detail(exc)
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
        before = len(st.session_state.get("sources") or [])
        result = client.upload_sources(files)
        sources = result.get("sources", [])
        _set_sources(sources)
        added = max(0, len(sources) - before)
        st.session_state.upload_error = None
        st.session_state.answer = None
        warnings = result.get("upload_warnings")
        st.session_state.upload_warnings = warnings
        st.success(f"Accepted {added} file(s). Active sources: {len(sources)}.")
    except (HTTPError, OSError, ValueError) as exc:
        st.session_state.upload_error = _error_detail(exc)
        st.session_state.upload_warnings = None
        # Refresh list in case a prior partial attach left sources on the server.
        try:
            if client.session_id:
                listed = client.list_sources()
                _set_sources(listed.get("sources", []))
        except (HTTPError, OSError, ValueError):
            pass

if st.session_state.get("upload_error"):
    st.error(st.session_state.upload_error)
if st.session_state.get("upload_warnings"):
    st.warning(f"Some files were skipped: {st.session_state.upload_warnings}")

sources = st.session_state.get("sources") or []
if sources:
    st.write("**Active sources**")
    filenames = [str(src.get("filename") or "unnamed") for src in sources]
    st.caption(", ".join(f"`{name}`" for name in filenames))
    for src in sources:
        name = src.get("filename") or "unnamed"
        rows = src.get("row_count", "?")
        cols = ", ".join(src.get("columns") or [])
        with st.expander(f"{name} — {rows} rows", expanded=False):
            st.write(f"Columns: {cols}")
            preview = src.get("preview_rows") or []
            if preview:
                st.dataframe(preview, use_container_width=True)
            else:
                st.caption("No preview rows available.")

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
    st.text_area(
        "Answer text",
        value=answer.get("text", ""),
        height=160,
        disabled=True,
        label_visibility="collapsed",
    )
    answer_files = answer.get("source_filenames") or []
    if answer_files:
        st.caption("Sources: " + ", ".join(answer_files))

st.divider()
st.caption(
    "Start the API with: `uv run uvicorn app.main:app --reload --port 8000` from `backend/`."
)
