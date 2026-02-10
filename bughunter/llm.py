"""Shared LLM helper with retry logic for Groq rate limits."""

from __future__ import annotations

import time
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage
from bughunter.config import GROQ_API_KEY, GROQ_MODEL


def get_llm(temperature: float = 0) -> ChatGroq:
    """Return a configured ChatGroq instance."""
    return ChatGroq(
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY,
        temperature=temperature,
    )


def invoke_with_retry(
    llm: ChatGroq,
    messages: list[BaseMessage],
    max_retries: int = 3,
    base_delay: float = 10.0,
) -> str:
    """Invoke the LLM with exponential backoff on rate-limit errors."""
    for attempt in range(max_retries):
        try:
            response = llm.invoke(messages)
            return response.content
        except Exception as e:
            error_str = str(e)
            if "rate_limit" in error_str or "413" in error_str or "429" in error_str:
                delay = base_delay * (2 ** attempt)
                print(f"  Rate limited (attempt {attempt + 1}/{max_retries}), retrying in {delay:.0f}s")
                time.sleep(delay)
            else:
                raise
    response = llm.invoke(messages)
    return response.content
