"""Dispatch a single LLM tool call to its handler.

Each handler validates input via the tool's Pydantic model, runs the
DB operation, and returns a JSON-serializable dict. Errors raise
`ToolDispatchError` so the chat router can surface them back to the
LLM as a tool_result with `is_error: true`.

Owner-scoped privacy: contacts are visible to (a) the owner, (b)
users in `shared_with`, or (c) any user when `is_private=False`.
Write/delete is owner-only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Contact, User
from app.services.tools import tool_input_model


class ToolDispatchError(RuntimeError):
    """Raised when a tool call fails validation or dispatch."""


def dispatch_tool_call(
    name: str,
    raw_input: dict[str, Any],
    user: User,
    db: Session,
) -> dict[str, Any]:
    model = tool_input_model(name)
    if model is None:
        raise ToolDispatchError(f"unknown tool: {name}")

    try:
        parsed = model.model_validate(raw_input)
    except ValidationError as exc:
        raise ToolDispatchError(f"invalid input for {name}: {exc}") from exc

    handler = _HANDLERS.get(name)
    if handler is None:
        raise ToolDispatchError(f"no handler registered for tool: {name}")
    return handler(parsed, user, db)


def _visible_contacts_query(user: User):
    return select(Contact).where(
        Contact.deleted_at.is_(None),
        or_(
            Contact.owner_id == user.id,
            Contact.is_private.is_(False),
            Contact.shared_with.any(user.id),
        ),
    )


def _serialize_contact(contact: Contact, user: User) -> dict[str, Any]:
    return {
        "id": contact.id,
        "name": contact.name,
        "email": contact.email,
        "cell_phone": contact.cell_phone,
        "office_phone": contact.office_phone,
        "title": contact.title,
        "company_name": contact.company_name,
        "contact_type": contact.contact_type,
        "country": contact.country,
        "notes": contact.notes,
        "is_private": contact.is_private,
        "is_self_owned": contact.owner_id == user.id,
        "owner_id": contact.owner_id,
    }


def _handle_search_contacts(params, user: User, db: Session) -> dict[str, Any]:
    query = _visible_contacts_query(user)
    if params.query:
        pattern = f"%{params.query.lower()}%"
        query = query.where(
            or_(
                func.lower(Contact.name).like(pattern),
                func.lower(func.coalesce(Contact.email, "")).like(pattern),
                func.lower(func.coalesce(Contact.company_name, "")).like(pattern),
                func.lower(func.coalesce(Contact.title, "")).like(pattern),
                func.lower(func.coalesce(Contact.notes, "")).like(pattern),
            )
        )
    if params.contact_type:
        query = query.where(Contact.contact_type == params.contact_type)
    rows = list(db.execute(query.limit(params.limit)).scalars())
    return {
        "results": [_serialize_contact(c, user) for c in rows],
        "limit": params.limit,
        "truncated": len(rows) == params.limit,
    }


def _handle_create_contact(params, user: User, db: Session) -> dict[str, Any]:
    contact = Contact(
        name=params.name,
        email=params.email,
        cell_phone=params.cell_phone,
        office_phone=params.office_phone,
        title=params.title,
        company_name=params.company_name,
        contact_type=params.contact_type,
        country=params.country,
        notes=params.notes,
        is_private=params.is_private,
        owner_id=user.id,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return {"created": _serialize_contact(contact, user)}


def _handle_update_contact(params, user: User, db: Session) -> dict[str, Any]:
    contact = db.get(Contact, params.contact_id)
    if contact is None or contact.deleted_at is not None:
        return {"error": "not_found", "contact_id": params.contact_id}
    if contact.owner_id != user.id:
        return {"error": "forbidden_owner_only", "contact_id": params.contact_id}

    updates = params.model_dump(exclude_unset=True, exclude={"contact_id"})
    for field, value in updates.items():
        setattr(contact, field, value)
    db.commit()
    db.refresh(contact)
    return {"updated": _serialize_contact(contact, user)}


def _handle_delete_contact(params, user: User, db: Session) -> dict[str, Any]:
    contact = db.get(Contact, params.contact_id)
    if contact is None or contact.deleted_at is not None:
        return {"error": "not_found", "contact_id": params.contact_id}
    if contact.owner_id != user.id:
        return {"error": "forbidden_owner_only", "contact_id": params.contact_id}
    contact.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return {"deleted_id": contact.id}


def _handle_pipeline_summary(params, user: User, db: Session) -> dict[str, Any]:
    base = (
        select(Contact.contact_type, func.count(Contact.id))
        .where(Contact.deleted_at.is_(None))
        .where(
            or_(
                Contact.owner_id == user.id,
                Contact.is_private.is_(False),
                Contact.shared_with.any(user.id),
            )
        )
        .group_by(Contact.contact_type)
    )
    if params.contact_type:
        base = base.where(Contact.contact_type == params.contact_type)
    rows = db.execute(base).all()
    return {
        "by_type": {row[0]: row[1] for row in rows},
        "total": sum(row[1] for row in rows),
    }


_HANDLERS = {
    "search_contacts": _handle_search_contacts,
    "create_contact": _handle_create_contact,
    "update_contact": _handle_update_contact,
    "delete_contact": _handle_delete_contact,
    "get_pipeline_summary": _handle_pipeline_summary,
}
