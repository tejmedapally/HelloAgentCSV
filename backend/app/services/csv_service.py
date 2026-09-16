"""CSV parsing and preview helpers for uploaded FAQ/policy files."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any, BinaryIO
from uuid import uuid4

import pandas as pd

from app.config import Settings, get_settings
from app.services.session_store import SourceRecord

# Common binary signatures that should never be treated as CSV text.
_BINARY_MAGIC = (
    b"\x89PNG",
    b"\xff\xd8\xff",  # JPEG
    b"%PDF",
    b"PK\x03\x04",  # ZIP / xlsx / docx
    b"\xd0\xcf\x11\xe0",  # OLE (xls/doc)
    b"\x1f\x8b",  # gzip
)


class CsvParseError(ValueError):
    """Raised when an upload cannot be turned into a usable DataFrame."""


def _preview_rows(df: pd.DataFrame, n: int) -> list[dict[str, Any]]:
    """Return the first n rows as JSON-serializable dicts."""
    if n <= 0 or df.empty:
        return []
    sample = df.head(n).where(pd.notnull(df.head(n)), None)
    return sample.to_dict(orient="records")


def _validate_filename(filename: str) -> str:
    if not filename or not str(filename).strip():
        raise CsvParseError("Filename is required.")
    name = Path(filename).name.strip()
    if not name:
        raise CsvParseError("Filename is required.")
    if name.lower().endswith((".xlsx", ".xls", ".xlsm", ".ods")):
        raise CsvParseError(
            f"'{name}' looks like a spreadsheet workbook. Export it as .csv and try again."
        )
    if not name.lower().endswith(".csv"):
        raise CsvParseError(
            f"Only .csv files are supported (got '{name}'). Rename or export as CSV."
        )
    return name


def _validate_raw_bytes(content: bytes, filename: str, cfg: Settings) -> None:
    if len(content) == 0:
        raise CsvParseError(f"'{filename}' is empty. Upload a CSV with a header and data rows.")

    max_bytes = cfg.max_upload_size_bytes
    if len(content) > max_bytes:
        raise CsvParseError(_format_size_limit_message(filename, len(content), cfg))

    head = content[:16]
    for magic in _BINARY_MAGIC:
        if head.startswith(magic):
            raise CsvParseError(
                f"'{filename}' is not a text CSV file (binary content detected)."
            )

    if b"\x00" in content[:8192]:
        raise CsvParseError(
            f"'{filename}' contains binary/null bytes and is not a valid CSV."
        )


def _drop_blank_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows that are entirely empty / whitespace / NaN."""
    if df.empty:
        return df

    def _cell_blank(value: Any) -> bool:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return True
        try:
            if pd.isna(value):
                return True
        except (TypeError, ValueError):
            pass
        if isinstance(value, str) and not value.strip():
            return True
        return False

    blank_row = df.apply(lambda col: col.map(_cell_blank)).all(axis=1)
    return df.loc[~blank_row].copy()


def _format_size_limit_message(filename: str, size_bytes: int, cfg: Settings) -> str:
    if size_bytes < 1024 * 1024:
        size_label = f"{size_bytes / 1024:.1f} KB"
    else:
        size_label = f"{size_bytes / (1024 * 1024):.1f} MB"
    return (
        f"'{filename}' is {size_label} and exceeds the "
        f"{cfg.max_upload_size_mb:g} MB upload limit."
    )


def parse_csv_bytes(
    content: bytes,
    filename: str,
    *,
    settings: Settings | None = None,
) -> SourceRecord:
    """Parse raw CSV bytes into a SourceRecord with preview rows.

    Rejects non-CSV filenames/content, oversized uploads, empty files, and
    CSVs with headers but no usable data rows.
    """
    cfg = settings or get_settings()
    name = _validate_filename(filename)
    _validate_raw_bytes(content, name, cfg)

    try:
        # Prefer utf-8; fall back to latin-1 for common Windows exports.
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("latin-1")

        # Sniff that the text has at least one delimiter-ish line before pandas.
        sample = text[:4096]
        if not sample.strip():
            raise CsvParseError(
                f"'{name}' has no usable content. Upload a CSV with a header and data rows."
            )
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = None

        read_kwargs: dict[str, Any] = {}
        if dialect is not None:
            read_kwargs["sep"] = dialect.delimiter
        df = pd.read_csv(io.StringIO(text), **read_kwargs)
    except CsvParseError:
        raise
    except Exception as exc:  # pandas/csv raise varied parse errors
        raise CsvParseError(
            f"'{name}' could not be parsed as CSV: {exc}"
        ) from exc

    if len(df.columns) == 0:
        raise CsvParseError(
            f"'{name}' has no columns. Expected a header row followed by data."
        )

    # Unnamed-only columns after a blank/broken parse usually means non-CSV text.
    named = [str(c) for c in df.columns if not str(c).startswith("Unnamed:")]
    if not named and not any(str(c).strip() for c in df.columns):
        raise CsvParseError(
            f"'{name}' does not look like a CSV with a usable header row."
        )

    df = _drop_blank_rows(df)
    if df.empty:
        raise CsvParseError(
            f"'{name}' has a header but no data rows. "
            "Add at least one data row before uploading."
        )

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
