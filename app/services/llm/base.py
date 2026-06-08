"""Provider-agnostic LLM abstraction used by the chat endpoint.

The `LLMProvider` Protocol is the single seam the rest of the app
talks to. Implementations (Gemini, Anthropic, …) convert their
native request and response types into the shared shapes defined
here so the orchestrator in `app.routers.chat` never imports a
vendor SDK directly.

Why a Protocol instead of an ABC: providers are duck-typed at use
sites; tests can drop in a `FakeLLMProvider` without inheriting.
Same pattern as `app.services.voice.tts_base.TTSProvider`.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol


# ---------------------------------------------------------------------------
# Response blocks
# ---------------------------------------------------------------------------


@dataclass
class LLMTextBlock:
    """Plain text segment in an assistant turn."""

    text: str
    type: Literal["text"] = "text"


@dataclass
class LLMToolUseBlock:
    """The model wants to call a tool with the given inputs."""

    id: str
    name: str
    input: dict[str, Any]
    type: Literal["tool_use"] = "tool_use"


LLMBlock = LLMTextBlock | LLMToolUseBlock


# ---------------------------------------------------------------------------
# Response envelope
# ---------------------------------------------------------------------------


@dataclass
class LLMUsage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class LLMResponse:
    """What every provider returns. Caller dispatches tools when
    `stop_reason == 'tool_use'`, otherwise treats text blocks as the
    final reply."""

    stop_reason: Literal["end_turn", "tool_use", "max_tokens", "stop_sequence"]
    content: list[LLMBlock]
    usage: LLMUsage = field(default_factory=LLMUsage)


# ---------------------------------------------------------------------------
# Input shape — minimal cross-provider message + tool-result wire format
# ---------------------------------------------------------------------------


# Messages flow through as plain dicts with a `role` and a `content`
# field. Content is either a string OR a list of typed sub-blocks
# (text, tool_use, or tool_result). Providers translate to native shape.
LLMMessage = dict[str, Any]


# Tool definitions are passed in as JSON-schema-style dicts:
#   {
#       "name": "search_contacts",
#       "description": "...",
#       "input_schema": {"type": "object", "properties": {...}, "required": [...]}
#   }
# This matches Anthropic's wire format. The Gemini provider converts
# to `function_declarations` at the boundary.
ToolDefinition = dict[str, Any]


# ---------------------------------------------------------------------------
# Provider Protocol
# ---------------------------------------------------------------------------


class LLMProviderError(RuntimeError):
    """Raised when a provider can't fulfill a request (config or upstream)."""


class LLMProvider(Protocol):
    """The contract every LLM backend implements."""

    async def call(
        self,
        *,
        messages: Sequence[LLMMessage],
        system: str,
        tools: Sequence[ToolDefinition] = (),
        on_tokens: Callable[[int, int], None] | None = None,
        max_tokens: int = 16000,
    ) -> LLMResponse: ...
