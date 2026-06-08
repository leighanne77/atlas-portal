"""GeminiProvider — implements LLMProvider against Google AI Studio.

Converts the cross-provider message + tool format defined in `base.py`
into Gemini's `generate_content` shape, then translates the response
back. Tool calls are surfaced as `LLMToolUseBlock` so chat.py's
dispatch loop is provider-agnostic.

Gemini → cross-provider mapping:
  - role "assistant" ⇄ Gemini "model"
  - text content ⇄ Part with text
  - tool_use ⇄ Part with function_call
  - tool_result (sub-block) ⇄ Part with function_response
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from typing import Any

from app.services.llm.base import (
    LLMMessage,
    LLMProviderError,
    LLMResponse,
    LLMTextBlock,
    LLMToolUseBlock,
    LLMUsage,
    ToolDefinition,
)

logger = logging.getLogger(__name__)


_FINISH_REASON_MAP = {
    "STOP": "end_turn",
    "MAX_TOKENS": "max_tokens",
    "OTHER": "end_turn",
    None: "end_turn",
}


class GeminiProvider:
    """Calls Gemini via the `google-generativeai` SDK."""

    def __init__(
        self,
        *,
        api_key: str,
        model_id: str = "gemini-1.5-pro",
    ) -> None:
        if not api_key:
            raise LLMProviderError("google_api_key not configured")
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise LLMProviderError(
                "google-generativeai not installed; "
                "add it to dependencies to use GeminiProvider"
            ) from exc

        genai.configure(api_key=api_key)
        self._genai = genai
        self._model_id = model_id

    async def call(
        self,
        *,
        messages: Sequence[LLMMessage],
        system: str,
        tools: Sequence[ToolDefinition] = (),
        on_tokens: Callable[[int, int], None] | None = None,
        max_tokens: int = 16000,
    ) -> LLMResponse:
        gemini_contents = [_to_gemini_content(m) for m in messages]
        gemini_tools = _to_gemini_tools(tools) if tools else None

        model = self._genai.GenerativeModel(
            model_name=self._model_id,
            system_instruction=system,
            tools=gemini_tools,
            generation_config={"max_output_tokens": max_tokens},
        )

        try:
            response = await model.generate_content_async(gemini_contents)
        except Exception as exc:
            raise LLMProviderError(f"Gemini request failed: {exc}") from exc

        usage = _extract_usage(response)
        if on_tokens is not None:
            on_tokens(usage.input_tokens, usage.output_tokens)

        return LLMResponse(
            stop_reason=_extract_stop_reason(response),
            content=_extract_blocks(response),
            usage=usage,
        )


# ---------------------------------------------------------------------------
# Translation helpers (cross-provider → Gemini)
# ---------------------------------------------------------------------------


def _to_gemini_content(message: LLMMessage) -> dict[str, Any]:
    """Convert one cross-provider message into a Gemini Content dict.

    Gemini uses "model" for assistant turns. Content blocks are
    "parts" — each part is either text, function_call, or
    function_response.
    """
    role = "model" if message["role"] == "assistant" else message["role"]
    raw_content = message["content"]

    if isinstance(raw_content, str):
        return {"role": role, "parts": [{"text": raw_content}]}

    parts: list[dict[str, Any]] = []
    for block in raw_content:
        block_type = block.get("type") if isinstance(block, dict) else getattr(block, "type", None)
        if block_type == "text":
            text = block["text"] if isinstance(block, dict) else block.text
            parts.append({"text": text})
        elif block_type == "tool_use":
            name = block["name"] if isinstance(block, dict) else block.name
            inputs = block["input"] if isinstance(block, dict) else block.input
            parts.append({"function_call": {"name": name, "args": inputs}})
        elif block_type == "tool_result":
            # chat.py emits {"type":"tool_result","tool_use_id":...,"content":...}
            # Gemini's function_response is keyed by name; we don't have
            # the name here, so fall back to tool_use_id as a stand-in.
            # When the model's prior turn already named the function,
            # Gemini correctly correlates by call_id internally.
            tool_use_id = block.get("tool_use_id", "tool")
            content = block.get("content", "")
            parts.append(
                {
                    "function_response": {
                        "name": tool_use_id,
                        "response": {"result": content},
                    }
                }
            )
        else:
            parts.append({"text": str(block)})
    return {"role": role, "parts": parts}


def _to_gemini_tools(tools: Sequence[ToolDefinition]) -> list[dict[str, Any]]:
    """Gemini wraps function declarations in a single `tools` object."""
    declarations: list[dict[str, Any]] = []
    for tool in tools:
        declarations.append(
            {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {"type": "object"}),
            }
        )
    return [{"function_declarations": declarations}]


# ---------------------------------------------------------------------------
# Translation helpers (Gemini → cross-provider)
# ---------------------------------------------------------------------------


def _extract_blocks(response: Any) -> list[Any]:
    """Walk Gemini's response and yield text + tool_use blocks."""
    blocks: list[Any] = []
    candidates = getattr(response, "candidates", []) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        if content is None:
            continue
        for part in getattr(content, "parts", []) or []:
            text = getattr(part, "text", None)
            if text:
                blocks.append(LLMTextBlock(text=text))
                continue
            fc = getattr(part, "function_call", None)
            if fc is not None and getattr(fc, "name", None):
                blocks.append(
                    LLMToolUseBlock(
                        id=f"call_{fc.name}_{len(blocks)}",
                        name=fc.name,
                        input=dict(fc.args) if fc.args else {},
                    )
                )
    return blocks


def _extract_stop_reason(response: Any) -> str:
    """Gemini's finish_reason → our stop_reason vocabulary."""
    candidates = getattr(response, "candidates", []) or []
    if not candidates:
        return "end_turn"
    finish = getattr(candidates[0], "finish_reason", None)
    finish_name = getattr(finish, "name", None) if finish is not None else None

    # If any part contains a function_call, tool_use takes precedence.
    content = getattr(candidates[0], "content", None)
    if content is not None:
        for part in getattr(content, "parts", []) or []:
            if getattr(part, "function_call", None) is not None:
                fc = part.function_call
                if getattr(fc, "name", None):
                    return "tool_use"

    return _FINISH_REASON_MAP.get(finish_name, "end_turn")


def _extract_usage(response: Any) -> LLMUsage:
    """Pull input/output token counts from the response metadata."""
    metadata = getattr(response, "usage_metadata", None)
    if metadata is None:
        return LLMUsage()
    return LLMUsage(
        input_tokens=getattr(metadata, "prompt_token_count", 0) or 0,
        output_tokens=getattr(metadata, "candidates_token_count", 0) or 0,
    )
