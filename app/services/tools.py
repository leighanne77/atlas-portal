"""LLM tool definitions for the chat router.

Pydantic input models double as the JSON-schema source so the wire
format the LLM sees stays in sync with the dispatcher's expectations.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SearchContactsInput(BaseModel):
    query: str | None = Field(
        default=None,
        description="Free-text search across name, email, company, title, notes.",
    )
    contact_type: str | None = Field(
        default=None,
        description="Filter to a specific contact_type (Client, Partner, Other).",
    )
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return.")


class CreateContactInput(BaseModel):
    name: str = Field(..., min_length=1, description="Full name.")
    email: str | None = Field(default=None)
    cell_phone: str | None = Field(default=None)
    office_phone: str | None = Field(default=None)
    title: str | None = Field(default=None)
    company_name: str | None = Field(default=None)
    contact_type: str = Field(default="Other")
    country: str | None = Field(default=None)
    notes: str | None = Field(default=None)
    is_private: bool = Field(default=False)


class UpdateContactInput(BaseModel):
    contact_id: int
    name: str | None = None
    email: str | None = None
    cell_phone: str | None = None
    office_phone: str | None = None
    title: str | None = None
    company_name: str | None = None
    contact_type: str | None = None
    country: str | None = None
    notes: str | None = None
    is_private: bool | None = None


class DeleteContactInput(BaseModel):
    contact_id: int


class PipelineSummaryInput(BaseModel):
    contact_type: str | None = Field(
        default=None, description="Optional filter to summarize one contact_type."
    )


class ToolSpec(BaseModel):
    name: str
    description: str
    input_model: type[BaseModel]


_TOOLS: list[ToolSpec] = [
    ToolSpec(
        name="search_contacts",
        description=(
            "Search the contact database. Use this whenever the user "
            "wants to find people, count contacts, or filter the list. "
            "Returns up to `limit` rows; the UI renders them as cards."
        ),
        input_model=SearchContactsInput,
    ),
    ToolSpec(
        name="create_contact",
        description=(
            "Add a new contact. Confirm at least the name and any "
            "key fields the user mentioned before calling."
        ),
        input_model=CreateContactInput,
    ),
    ToolSpec(
        name="update_contact",
        description=(
            "Update fields on an existing contact, identified by "
            "contact_id. Only fields the user wants to change need "
            "to be set; leave others null."
        ),
        input_model=UpdateContactInput,
    ),
    ToolSpec(
        name="delete_contact",
        description=(
            "Permanently soft-delete a contact (sets deleted_at). "
            "ALWAYS confirm with the user before calling this."
        ),
        input_model=DeleteContactInput,
    ),
    ToolSpec(
        name="get_pipeline_summary",
        description=(
            "Return aggregate counts by contact_type. Useful for "
            "'how many clients do we have?' style questions."
        ),
        input_model=PipelineSummaryInput,
    ),
]


def llm_tool_definitions() -> list[dict[str, Any]]:
    """JSON-schema tool list passed to the LLM provider.

    Anthropic and our shared types both use:
      {"name": str, "description": str, "input_schema": JSONSchema}
    The Gemini provider re-shapes this into Gemini's
    `function_declarations` format at the boundary.
    """
    definitions: list[dict[str, Any]] = []
    for spec in _TOOLS:
        schema = spec.input_model.model_json_schema()
        schema.pop("title", None)
        definitions.append(
            {
                "name": spec.name,
                "description": spec.description,
                "input_schema": schema,
            }
        )
    return definitions


def tool_input_model(name: str) -> type[BaseModel] | None:
    for spec in _TOOLS:
        if spec.name == name:
            return spec.input_model
    return None
