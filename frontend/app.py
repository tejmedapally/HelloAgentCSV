"""Grounded FAQ — Streamlit UI for CSV upload and data-only Q&A."""

from __future__ import annotations

import os

import streamlit as st
from httpx import HTTPError, HTTPStatusError

from api_client import BackendClient
from ui_chrome import inject_styles, render_footer, render_header, section_header

st.set_page_config(
    page_title="Grounded FAQ",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_styles()
render_header()


def _app_password() -> str:
    return (os.getenv("APP_PASSWORD") or "").strip()


def _get_client() -> BackendClient:
    if "backend_client" not in st.session_state:
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

    st.info("Enter the shared access password to use Grounded FAQ.")
    with st.form("login_form"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", type="primary")
    if submitted:
        if password == expected:
            st.session_state.authenticated = True
            st.rerun()
        st.error("Incorrect password.")
    render_footer()
    st.stop()


_require_login()

client = _get_client()
if "sources" not in st.session_state:
    st.session_state.sources = []

sources = st.session_state.get("sources") or []
has_sources = bool(sources)

# Upload | Ask | Answer — one row, equal-height panels
PANEL_HEIGHT = 460
col_up, col_ask, col_ans = st.columns(3, gap="medium")

with col_up:
    with st.container(border=True, height=PANEL_HEIGHT):
        section_header("1 · Upload CSV")
        st.caption("Choose CSV files")
        uploads = st.file_uploader(
            "Choose CSV files",
            type=["csv"],
            accept_multiple_files=True,
            help="Select one or more .csv files",
            label_visibility="collapsed",
        )
        upload_col, clear_col = st.columns([2, 1])
        with upload_col:
            upload_clicked = st.button(
                "Upload",
                type="primary",
                disabled=not uploads,
                use_container_width=True,
            )
        with clear_col:
            clear_clicked = st.button(
                "Clear",
                disabled=not st.session_state.get("session_id"),
                use_container_width=True,
            )
        if has_sources:
            names = [str(s.get("filename") or "unnamed") for s in sources]
            st.caption("Active: " + ", ".join(names))

with col_ask:
    with st.container(border=True, height=PANEL_HEIGHT):
        section_header("2 · Ask a question")
        if not has_sources:
            st.caption("Upload at least one CSV first.")
        question = st.text_area(
            "Question",
            placeholder="e.g. What is the return window? What are visiting hours?",
            height=110,
            disabled=not has_sources,
        )
        can_ask = has_sources and bool((question or "").strip())
        ask_clicked = st.button(
            "Ask", type="primary", disabled=not can_ask, use_container_width=True
        )

with col_ans:
    with st.container(border=True, height=PANEL_HEIGHT):
        section_header("3 · Answer")
        st.caption("Select the text below to copy.")
        answer = st.session_state.get("answer")
        if answer:
            status = str(answer.get("status") or "")
            st.caption(f"Status: {_status_label(status)}")
            st.code(str(answer.get("text") or ""), language=None)
            answer_files = answer.get("source_filenames") or []
            if answer_files:
                st.caption("Based on: " + ", ".join(answer_files))
        else:
            st.caption("Your answer will appear here after you ask.")

# --- Actions (rerun after state changes so Ask / Answer update immediately) ---
if upload_clicked and uploads:
    try:
        _ensure_session(client)
        files = [(f.name, f.getvalue()) for f in uploads]
        result = client.upload_sources(files)
        sources_out = result.get("sources", [])
        _set_sources(sources_out)
        st.session_state.upload_error = None
        st.session_state.answer = None
        st.session_state.upload_warnings = result.get("upload_warnings")
        st.session_state.flash_success = (
            f"Accepted upload. Active sources: {len(sources_out)}."
        )
        st.rerun()
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
        st.session_state.flash_success = "Sources cleared."
        st.rerun()
    except (HTTPError, OSError, ValueError) as exc:
        st.session_state.upload_error = _error_detail(exc)

if ask_clicked and has_sources and (question or "").strip():
    try:
        _ensure_session(client)
        with st.spinner("Looking up your files…"):
            answer = client.ask(question)
        st.session_state.answer = answer
        st.session_state.ask_error = None
        st.rerun()
    except (HTTPError, OSError, ValueError) as exc:
        st.session_state.ask_error = _error_detail(exc)
        st.session_state.answer = None

# One-shot status from previous action (set before st.rerun)
_flash = st.session_state.pop("flash_success", None)
if _flash:
    st.success(_flash)

if st.session_state.get("upload_error"):
    st.error(st.session_state.upload_error)
if st.session_state.get("upload_warnings"):
    st.warning(f"Some files were skipped: {st.session_state.upload_warnings}")
if st.session_state.get("ask_error"):
    st.error(st.session_state.ask_error)

if sources:
    with st.expander("Preview sources", expanded=False):
        for src in sources:
            name = src.get("filename") or "unnamed"
            rows = src.get("row_count", "?")
            cols = ", ".join(src.get("columns") or [])
            st.markdown(f"**{name}** — {rows} rows")
            st.caption(f"Columns: {cols}")
            preview = src.get("preview_rows") or []
            if preview:
                st.dataframe(preview, use_container_width=True, height=160)

with st.expander("How to use", expanded=False):
    st.markdown(
        "1. **Upload** one or more CSV files.  \n"
        "2. **Ask** a question in plain English.  \n"
        "3. **Copy** the answer from the Answer panel."
    )

with st.expander("Connection & session", expanded=False):
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
        st.caption(f"Session: `{session_id}`")
        if st.button("Refresh sources"):
            try:
                listed = client.list_sources(session_id)
                _set_sources(listed.get("sources", []))
                st.session_state.session_error = None
                st.rerun()
            except (HTTPError, OSError, ValueError) as exc:
                st.session_state.session_error = _error_detail(exc)
    else:
        st.caption("No session yet — created automatically on upload.")

    if st.session_state.get("session_error"):
        st.error(st.session_state.session_error)

render_footer()
