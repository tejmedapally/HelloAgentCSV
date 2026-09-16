"""CSV parsing and preview helpers for uploaded FAQ/policy files."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, BinaryIO
from uuid import uuid4

import pandas as pd

from app.config import Settings, get_settings
from app.services.session_store import SourceRecord


class CsvParseError(ValueError):
    """Raised when an upload cannot be turned into a usable DataFrame."""


def _preview_rows(df: pd.DataFrame, n: int) -> list[dict[str, Any]]:
    """Return the first n rows as JSON-serializable dicts."""
    if n <= 0 or df.empty:
        return []
    sample = df.head(n).where(pd.notnull(df.head(n)), None)
    return sample.to_dict(orient="records")


def parse_csv_bytes(
    content: bytes,
    filename: str,
    *,
    settings: Settings | None = None,
) -> SourceRecord:
    """Parse raw CSV bytes into a SourceRecord with preview rows.

    Basic checks only (size, non-empty parse). Stricter validation is T020.
    """
    cfg = settings or get_settings()

    if not filename or not str(filename).strip():
        raise CsvParseError("Filename is required")

    name = Path(filename).name
    if not name.lower().endswith(".csv"):
        raise CsvParseError("Only .csv files are supported")

    if len(content) == 0:
        raise CsvParseError("Uploaded file is empty")

    if len(content) > cfg.max_upload_size_bytes:
        raise CsvParseError(
            f"File exceeds max upload size of {cfg.max_upload_size_mb} MB"
        )

    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:  # pandas raises varied parse errors
        raise CsvParseError(f"Could not parse CSV: {exc}") from exc

    if df.empty and len(df.columns) == 0:
        raise CsvParseError("CSV has no columns or data")

    columns = [str(c) for c in df.columns.tolist()]
    row_count = int(len(df))
    preview = _preview_rows(df, cfg.preview_row_count)

    return SourceRecord(
        id=str(uuid4()),
        filename=name,
        columns=columns,
        row_count=row_count,
        preview_rows=preview,
        dataframe=df,
    )


def parse_csv_file(
    file_obj: BinaryIO,
    filename: str,
    *,
    settings: Settings | None = None,
) -> SourceRecord:
    """Parse a file-like object (e.g. UploadFile.file) into a SourceRecord."""
    content = file_obj.read()
    if isinstance(content, str):
        content = content.encode("utf-8")
    return parse_csv_bytes(content, filename, settings=settings)
