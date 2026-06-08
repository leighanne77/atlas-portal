"""Initial schema — users, contacts, voice_usage.

Single squashed migration for the portfolio repo. The original
project carried 15+ incremental migrations; that history was
collapsed into this one so a fresh clone can `alembic upgrade head`
into the simplified schema in one shot.

Revision ID: 0001
Revises:
Create Date: 2026-06-08 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("google_user_id", sa.String(255), nullable=True, unique=True),
        sa.Column("role", sa.String(50), nullable=False, server_default="member"),
        sa.Column(
            "intro_seen", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "daily_input_tokens_used",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "daily_output_tokens_used",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("token_budget_reset_at", sa.Date(), nullable=True),
        sa.Column(
            "daily_input_token_budget_override", sa.Integer(), nullable=True
        ),
        sa.Column(
            "daily_voice_minutes_budget_override", sa.Integer(), nullable=True
        ),
        sa.Column("google_access_token", sa.String(1024), nullable=True),
        sa.Column("google_refresh_token", sa.String(1024), nullable=True),
    )

    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("cell_phone", sa.String(20), nullable=True),
        sa.Column("office_phone", sa.String(20), nullable=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "owner_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "is_private",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "shared_with",
            postgresql.ARRAY(sa.Integer()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "contact_type",
            sa.String(50),
            nullable=False,
            server_default="Other",
        ),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_contacts_owner_id", "contacts", ["owner_id"], unique=False
    )

    op.create_table(
        "voice_usage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "ts",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("mode", sa.String(4), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("model_id", sa.String(64), nullable=False),
        sa.Column("duration_sec", sa.Float(), nullable=True),
        sa.Column("char_count", sa.Integer(), nullable=True),
        sa.Column(
            "cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"
        ),
        sa.CheckConstraint(
            "mode IN ('stt', 'tts')", name="voice_usage_mode_check"
        ),
    )
    op.create_index(
        "ix_voice_usage_user_ts", "voice_usage", ["user_id", "ts"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_voice_usage_user_ts", table_name="voice_usage")
    op.drop_table("voice_usage")
    op.drop_index("ix_contacts_owner_id", table_name="contacts")
    op.drop_table("contacts")
    op.drop_table("users")
