"""Provider-agnostic LLM access for the chat endpoint.

Public API:
  - call_llm(...)          → LLMResponse (the orchestrator's entry point)
  - get_default_provider() → returns the LLMProvider selected by config
  - LLMResponse, LLMTextBlock, LLMToolUseBlock, LLMUsage (response types)
  - LLMProvider, LLMProviderError (Protocol + error type)

Provider selection is driven by `settings.llm_provider` ("gemini" by
default, "anthropic" supported). Tests can monkeypatch
`get_default_provider` to inject a fake.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from app.config import get_settings
from app.services.llm.base import (
    LLMBlock,
    LLMMessage,
    LLMProvider,
    LLMProviderError,
    LLMResponse,
    LLMTextBlock,
    LLMToolUseBlock,
    LLMUsage,
    ToolDefinition,
)

__all__ = [
    "LLMBlock",
    "LLMMessage",
    "LLMProvider",
    "LLMProviderError",
    "LLMResponse",
    "LLMTextBlock",
    "LLMToolUseBlock",
    "LLMUsage",
    "ToolDefinition",
    "call_llm",
    "get_default_provider",
]


def get_default_provider() -> LLMProvider:
    """Build the configured provider from settings.

    Module-level so tests can monkeypatch this to inject a fake
    without touching the orchestrator's call signature.
    """
    settings = get_settings()
    name = settings.llm_provider.lower()
    if name == "gemini":
        from app.services.llm.gemini_provider import GeminiProvider

        return GeminiProvider(
            api_key=settings.google_api_key,
            model_id=settings.llm_model,
        )
    if name == "anthropic":
        from app.services.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model_id=settings.llm_model,
        )
    raise LLMProviderError(f"unknown llm_provider: {settings.llm_provider}")


async def call_llm(
    *,
    messages: Sequence[LLMMessage],
    system: str,
    tools: Sequence[ToolDefinition] = (),
    on_tokens: Callable[[int, int], None] | None = None,
    max_tokens: int = 16000,
    provider: LLMProvider | None = None,
) -> LLMResponse:
    """Dispatch to the configured provider. Tests can inject `provider`."""
    provider = provider or get_default_provider()
    return await provider.call(
        messages=messages,
        system=system,
        tools=tools,
        on_tokens=on_tokens,
        max_tokens=max_tokens,
    )
