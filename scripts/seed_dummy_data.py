"""Seed the database with Faker-generated demo contacts.

Usage:
    python -m scripts.seed_dummy_data

Idempotent on users (won't duplicate); appends 25 contacts each
time it runs.
"""

from __future__ import annotations

import random

from faker import Faker

from app.database import SessionLocal
from app.models import Contact, User

CONTACT_TYPES = ["Client", "Partner", "Vendor", "Advisor", "Other"]
COUNTRIES = [
    "United States",
    "Canada",
    "United Kingdom",
    "Germany",
    "Japan",
    "Australia",
    None,
]


def _get_or_create_user(db, email: str, name: str, role: str) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        return existing
    user = User(email=email, name=name, role=role, intro_seen=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def main() -> None:
    fake = Faker()
    Faker.seed(42)
    random.seed(42)

    db = SessionLocal()
    try:
        admin = _get_or_create_user(
            db, "admin@example.com", "Demo Admin", role="admin"
        )
        member = _get_or_create_user(
            db, "demo@example.com", "Demo User", role="member"
        )

        for i in range(25):
            owner = admin if i % 2 == 0 else member
            contact = Contact(
                name=fake.name(),
                email=fake.email(),
                cell_phone=fake.phone_number(),
                title=fake.job(),
                company_name=fake.company(),
                contact_type=random.choice(CONTACT_TYPES),
                country=random.choice(COUNTRIES),
                notes=fake.sentence(nb_words=10),
                is_private=random.random() < 0.2,
                owner_id=owner.id,
            )
            db.add(contact)
        db.commit()
        print("Seeded 25 contacts across 2 demo users.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
