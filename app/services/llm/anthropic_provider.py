"""AnthropicProvider — implements LLMProvider against Claude.

Kept alongside the Gemini default to demonstrate the abstraction:
swap the provider via config, no code change in the orchestrator.
Anthropic's wire format is what the cross-provider types in `base.py`
were originally shaped around, so this provider is a thin pass-through.
"""

from __future__ import annotations

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


class AnthropicProvider:
    """Calls Anthropic's API via the `anthropic` SDK."""

    def __init__(
        self,
        *,
        api_key: str,
        model_id: str = "claude-sonnet-4-6",
    ) -> None:
        if not api_key:
            raise LLMProviderError("anthropic_api_key not configured")
        try:
            from anthropic import AsyncAnthropic
        except ImportError as exc:
            raise LLMProviderError(
                "anthropic not installed; "
                "add it to dependencies to use AnthropicProvider"
            ) from exc

        self._client = AsyncAnthropic(api_key=api_key)
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
        request_kwargs: dict[str, Any] = {
            "model": self._model_id,
            "max_tokens": max_tokens,
            "system": system,
            "messages": list(messages),
        }
        if tools:
            request_kwargs["tools"] = list(tools)

        try:
            response = await self._client.messages.create(**request_kwargs)
        except Exception as exc:
            raise LLMProviderError(f"Anthropic request failed: {exc}") from exc

        usage = LLMUsage(
            input_tokens=getattr(response.usage, "input_tokens", 0) or 0,
            output_tokens=getattr(response.usage, "output_tokens", 0) or 0,
        )
        if on_tokens is not None:
            on_tokens(usage.input_tokens, usage.output_tokens)

        return LLMResponse(
            stop_reason=_map_stop_reason(response.stop_reason),
            content=_extract_blocks(response.content),
            usage=usage,
        )


_STOP_REASON_MAP = {
    "end_turn": "end_turn",
    "tool_use": "tool_use",
    "max_tokens": "max_tokens",
    "stop_sequence": "stop_sequence",
    None: "end_turn",
}


def _map_stop_reason(reason: str | None) -> str:
    return _STOP_REASON_MAP.get(reason, "end_turn")


def _extract_blocks(content: list[Any]) -> list[Any]:
    blocks: list[Any] = []
    for block in content:
        btype = getattr(block, "type", None)
        if btype == "text":
            blocks.append(LLMTextBlock(text=block.text))
        elif btype == "tool_use":
            blocks.append(
                LLMToolUseBlock(
                    id=block.id,
                    name=block.name,
                    input=dict(block.input),
                )
            )
    return blocks
