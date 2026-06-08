"""Contact CRUD endpoints.

Reads honor the owner/public/shared_with visibility filter. Writes
(PATCH/DELETE) require ownership — 404 when the contact isn't
visible at all (don't reveal existence), 403 when visible but the
caller doesn't own it.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Contact, User

router = APIRouter(
    prefix="/contacts",
    tags=["contacts"],
    dependencies=[Depends(get_current_user)],
)


class ContactRead(BaseModel):
    id: int
    name: str
    email: str | None = None
    cell_phone: str | None = None
    office_phone: str | None = None
    title: str | None = None
    company_name: str | None = None
    contact_type: str
    country: str | None = None
    notes: str | None = None
    is_private: bool
    owner_id: int

    class Config:
        from_attributes = True


class ContactCreate(BaseModel):
    name: str
    email: str | None = None
    cell_phone: str | None = None
    office_phone: str | None = None
    title: str | None = None
    company_name: str | None = None
    contact_type: str = "Other"
    country: str | None = None
    notes: str | None = None
    is_private: bool = False


class ContactUpdate(BaseModel):
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


def _visible_contacts_query(user: User):
    return select(Contact).where(
        Contact.deleted_at.is_(None),
        or_(
            Contact.owner_id == user.id,
            Contact.is_private.is_(False),
            Contact.shared_with.any(user.id),
        ),
    )


def _load_visible_contact(contact_id: int, db: Session, current_user: User) -> Contact:
    stmt = _visible_contacts_query(current_user).where(Contact.id == contact_id)
    contact = db.scalars(stmt).first()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return contact


def _require_owner(contact: Contact, current_user: User) -> None:
    if contact.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


@router.get("", response_model=list[ContactRead])
def list_contacts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Contact]:
    return list(db.scalars(_visible_contacts_query(current_user)))


@router.get("/{contact_id}", response_model=ContactRead)
def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Contact:
    return _load_visible_contact(contact_id, db, current_user)


@router.post("", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(
    body: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Contact:
    contact = Contact(**body.model_dump(), owner_id=current_user.id)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.patch("/{contact_id}", response_model=ContactRead)
def update_contact(
    contact_id: int,
    body: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Contact:
    contact = _load_visible_contact(contact_id, db, current_user)
    _require_owner(contact, current_user)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    contact = _load_visible_contact(contact_id, db, current_user)
    _require_owner(contact, current_user)
    contact.deleted_at = datetime.now(timezone.utc)
    db.commit()
