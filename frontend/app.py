"""Hello Agent — Streamlit UI for CSV upload and FAQ ask."""

from __future__ import annotations

import os

import streamlit as st
from httpx import HTTPError, HTTPStatusError

from api_client import BackendClient

st.set_page_config(
    page_title="Hello Agent",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.title("Hello Agent")
st.caption("Answers come only from your uploaded CSV files — not from general knowledge.")


def _app_password() -> str:
    return (os.getenv("APP_PASSWORD") or "").strip()


def _require_login() -> None:
    """Shared-password gate. Skipped when APP_PASSWORD is unset (local/dev)."""
    expected = _app_password()
    if not expected:
        return
    if st.session_state.get("authenticated"):
        with st.sidebar:
            if st.button("Log out", use_container_width=True):
                st.session_state.authenticated = False
                st.rerun()
        return

    st.info("Enter the shared access password to use Hello Agent.")
    with st.form("login_form"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", type="primary")
    if submitted:
        if password == expected:
            st.session_state.authenticated = True
            st.rerun()
        st.error("Incorrect password.")
    st.stop()


_require_login()

st.info(
    "**How to use:**  \n"
    "1. **Upload** one or more CSV files and confirm the preview.  \n"
    "2. **Ask** a question in plain English.  \n"
    "3. **Copy** the answer into email or chat."
)


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


def _status_label(status: str) -> str:
    labels = {
        "ok": "Found in uploaded data",
        "not_found": "Not found in uploaded data",
        "error": "Could not answer",
    }
    return labels.get(status, status or "unknown")


client = _get_client()

# --- Primary flow: Upload → Ask → Answer ---

st.header("1. Upload")
st.write("Add FAQ, policy, or product CSV files. Open a file below to preview the first rows.")

uploads = st.file_uploader(
    "CSV files",
    type=["csv"],
    accept_multiple_files=True,
    label_visibility="collapsed",
    help="Select one or more .csv files from your computer.",
)

upload_col, clear_col = st.columns([2, 1])
with upload_col:
    upload_clicked = st.button(
        "Upload to session",
        type="primary",
        disabled=not uploads,
        use_container_width=True,
    )
with clear_col:
    clear_clicked = st.button(
        "Clear all sources",
        disabled=not st.session_state.get("session_id"),
        use_container_width=True,
    )

if upload_clicked and uploads:
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
        try:
            if client.session_id:
                listed = client.list_sources()
                _set_sources(listed.get("sources", []))
        except (HTTPError, OSError, ValueError):
            pass

if clear_clicked:
    try:
        sid = _ensure_session(client)
        client.clear_sources(sid)
        _set_sources([])
        st.session_state.answer = None
        st.session_state.upload_error = None
        st.session_state.upload_warnings = None
        st.session_state.ask_error = None
        st.success("All sources cleared. Upload a CSV before asking again.")
    except (HTTPError, OSError, ValueError) as exc:
        st.session_state.upload_error = _error_detail(exc)

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
        with st.expander(f"{name} — {rows} rows", expanded=len(sources) == 1):
            st.write(f"Columns: {cols}")
            preview = src.get("preview_rows") or []
            if preview:
                st.dataframe(preview, use_container_width=True)
            else:
                st.caption("No preview rows available.")
else:
    st.caption("No files uploaded yet.")

st.divider()
st.header("2. Ask")
st.write("Type a support-style question. Answers use only the active CSVs above.")

has_sources = bool(sources)
if not has_sources:
    st.warning("Upload at least one CSV in **Upload** before you can ask.")

question = st.text_area(
    "Your question",
    placeholder="e.g. What is the return window? What are visiting hours?",
    height=100,
    disabled=not has_sources,
)

can_ask = has_sources and bool(question.strip())
if has_sources and not question.strip():
    st.caption("Enter a question, then click Ask.")

if st.button("Ask", type="primary", disabled=not can_ask):
    try:
        _ensure_session(client)
        with st.spinner("Looking up your files…"):
            answer = client.ask(question)
        st.session_state.answer = answer
        st.session_state.ask_error = None
    except (HTTPError, OSError, ValueError) as exc:
        st.session_state.ask_error = _error_detail(exc)
        st.session_state.answer = None

if st.session_state.get("ask_error"):
    st.error(st.session_state.ask_error)

st.divider()
st.header("3. Answer")
st.write("Select the text below and copy it for email or chat.")

answer = st.session_state.get("answer")
if answer:
    status = str(answer.get("status") or "")
    st.caption(f"Status: {_status_label(status)} (`{status or 'unknown'}`)")
    answer_text = str(answer.get("text") or "")
    # st.code keeps full text visible and easy to select/copy in one action.
    st.code(answer_text, language=None)
    answer_files = answer.get("source_filenames") or []
    if answer_files:
        st.caption("Based on: " + ", ".join(answer_files))
else:
    st.caption("Your answer will appear here after you ask a question.")

# --- Secondary: connection / session diagnostics ---
st.divider()
with st.expander("Connection & session (optional)", expanded=False):
    st.write(f"**BACKEND_URL:** `{client.base_url}`")
    diag1, diag2 = st.columns(2)
    with diag1:
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
    with diag2:
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

    session_id = st.session_state.get("session_id")
    if session_id:
        st.info(f"Session ID: `{session_id}`")
        if st.button("Refresh sources from backend"):
            try:
                listed = client.list_sources(session_id)
                _set_sources(listed.get("sources", []))
                st.session_state.session_error = None
            except (HTTPError, OSError, ValueError) as exc:
                st.session_state.session_error = _error_detail(exc)
    else:
        st.caption("No session yet — one is created automatically on upload.")

    if st.session_state.get("session_error"):
        st.error(st.session_state.session_error)

    st.caption(
        "Start the API with: `uv run uvicorn app.main:app --reload --port 8000` from `backend/`."
    )
