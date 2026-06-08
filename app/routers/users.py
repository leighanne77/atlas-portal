"""User profile endpoints (current user only — no admin operations)."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_current_user)],
)


class UserMeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str | None = None
    role: str
    intro_seen: bool


@router.get("/me", response_model=UserMeResponse)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me/intro-seen", status_code=204)
def mark_intro_seen(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    current_user.intro_seen = True
    db.commit()
