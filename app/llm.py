"""Shared LLM client utilities for Interflow agents and governance."""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
# Default to sonnet for cost efficiency in this multi-agent system.
# Override via INTERFLOW_MODEL env var (e.g. "claude-opus-4-6" for highest quality).
AGENT_MODEL = os.getenv("INTERFLOW_MODEL", "claude-sonnet-4-6")

# ---------------------------------------------------------------------------
# System prompt — loaded once from prompts/system_prompt.md
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_prompt.md"
SYSTEM_PROMPT: str = (
    _SYSTEM_PROMPT_PATH.read_text()
    if _SYSTEM_PROMPT_PATH.exists()
    else (
        "You are an agent in the Interflow multi-lens sensemaking platform. "
        "Treat all meta-model outputs as hypotheses, not facts. "
        "Always include confidence, alternatives, and missing_information in outputs."
    )
)

# ---------------------------------------------------------------------------
# Lazy singleton Anthropic client
# ---------------------------------------------------------------------------
_client = None


def get_client():
    """Return (or create) the shared Anthropic client."""
    global _client
    if _client is None:
        try:
            import anthropic  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "The 'anthropic' package is required for LLM agent calls. "
                "Install it with: pip install anthropic>=0.40.0"
            ) from exc
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment
    return _client


# ---------------------------------------------------------------------------
# Core call helper
# ---------------------------------------------------------------------------

def call_agent(prompt: str, max_tokens: int = 2000) -> str:
    """Make a streaming LLM call and return the complete text response."""
    client = get_client()
    with client.messages.stream(
        model=AGENT_MODEL,
        max_tokens=max_tokens,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = stream.get_final_message()
    return next(b.text for b in message.content if b.type == "text")


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------

def extract_json(text: str) -> dict:
    """Extract the first JSON object from LLM response text.

    Handles:
    - Pure JSON responses
    - JSON inside ```json ... ``` code blocks
    - JSON embedded anywhere in text
    """
    # 1. Try markdown code blocks (```json or ```)
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        candidate = match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # 2. Try to find a raw JSON object
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    # 3. Last resort — attempt full text parse
    return json.loads(text)


# ---------------------------------------------------------------------------
# Agent prompt template
# ---------------------------------------------------------------------------

AGENT_PROMPT_TEMPLATE = """\
You are {agent_name} in the Interflow platform.

MISSION
{mission}

INPUTS
{inputs}

RULES
1) Separate observation from interpretation.
2) Treat all lens outputs as hypotheses, not facts.
3) Never output fixed developmental/stage/color identity labels for people or teams.
4) Escalate (set confidence < 0.5 and flag missing_information) when evidence is thin.
5) Return ONLY valid JSON matching the output schema — no preamble, no explanation.

OUTPUT SCHEMA
{output_schema}
"""
