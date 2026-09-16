"""Claude + LangChain pandas dataframe agent (data-only answers)."""

from __future__ import annotations

import re
from typing import Sequence

from langchain_anthropic import ChatAnthropic
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

from app.config import Settings, get_settings
from app.models.schemas import AnswerStatus, AskResponse
from app.services.session_store import SourceRecord

NOT_FOUND_PHRASE = "I could not find this information in the uploaded files"

DATA_ONLY_PREFIX = f"""You are Hello Agent, a support assistant that answers ONLY from the
provided CSV table(s) loaded as pandas DataFrames.

Strict rules:
- Use only values present in the DataFrame(s). Do not use general world knowledge.
- Do not invent policies, FAQs, numbers, or product details.
- Prefer clear English answers suitable to copy into email or chat.
- For text questions, quote or paraphrase the relevant cell/row content.
- For numeric questions, compute simple aggregates (sum, average, count) from the tables when needed.
- If the answer is not in the data, reply with exactly:
  {NOT_FOUND_PHRASE}
- Keep reasoning grounded in the tables; do not speculate.
"""

_NOT_FOUND_RE = re.compile(
    re.escape(NOT_FOUND_PHRASE) + r"|could not find this information|not found in the uploaded",
    re.IGNORECASE,
)


def _build_llm(settings: Settings) -> ChatAnthropic:
    if not settings.anthropic_api_key.strip():
        raise ValueError(
            "ANTHROPIC_API_KEY is not set. Add it to backend/.env before asking questions."
        )
    return ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=settings.llm_temperature,
    )


def _classify_answer(text: str) -> AnswerStatus:
    if _NOT_FOUND_RE.search(text or ""):
        return AnswerStatus.not_found
    return AnswerStatus.ok


def answer_from_sources(
    sources: Sequence[SourceRecord],
    question: str,
    *,
    settings: Settings | None = None,
) -> AskResponse:
    """Run the dataframe agent against active session sources."""
    cfg = settings or get_settings()
    q = (question or "").strip()
    if not q:
        return AskResponse(
            text="Please enter a non-empty question.",
            status=AnswerStatus.error,
            source_filenames=[],
        )
    if not sources:
        return AskResponse(
            text="Upload one or more CSV files before asking a question.",
            status=AnswerStatus.error,
            source_filenames=[],
        )

    filenames = [s.filename for s in sources]
    frames = [s.dataframe for s in sources]
    # Single frame vs list — agent accepts either
    df_arg = frames[0] if len(frames) == 1 else list(frames)

    try:
        llm = _build_llm(cfg)
        agent = create_pandas_dataframe_agent(
            llm,
            df_arg,
            agent_type="tool-calling",
            prefix=DATA_ONLY_PREFIX,
            verbose=False,
            allow_dangerous_code=True,
            include_df_in_prompt=True,
            number_of_head_rows=min(5, cfg.preview_row_count),
            max_iterations=12,
        )
        result = agent.invoke({"input": q})
        if isinstance(result, dict):
            text = str(result.get("output") or result.get("result") or result)
        else:
            text = str(result)
        text = text.strip() or NOT_FOUND_PHRASE
        status = _classify_answer(text)
        return AskResponse(
            text=text,
            status=status,
            source_filenames=filenames,
        )
    except ValueError as exc:
        return AskResponse(
            text=str(exc),
            status=AnswerStatus.error,
            source_filenames=filenames,
        )
    except Exception as exc:  # provider / agent failures
        return AskResponse(
            text=f"Could not generate an answer: {exc}",
            status=AnswerStatus.error,
            source_filenames=filenames,
        )
