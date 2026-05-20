"""Initial SocialHealth schema.

Revision ID: 20260520_0001
Revises:
Create Date: 2026-05-20
"""

from alembic import op
import sqlalchemy as sa


revision = "20260520_0001"
down_revision = None
branch_labels = None
depends_on = None


task_difficulty = sa.Enum("easy", "medium", "hard", name="task_difficulty")
achievement_condition_type = sa.Enum(
    "streak",
    "total_entries",
    "tasks_completed",
    "level_reached",
    "xp_earned",
    name="achievement_condition_type",
)


def upgrade():
    task_difficulty.create(op.get_bind(), checkfirst=True)
    achievement_condition_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("longest_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_activity_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("title_en", sa.String(length=200), nullable=True),
        sa.Column("description_en", sa.String(length=1000), nullable=True),
        sa.Column("difficulty", task_difficulty, nullable=False),
        sa.Column("xp_reward", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("min_anxiety", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_anxiety", sa.Integer(), nullable=False, server_default="10"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "achievements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("icon", sa.String(length=10), nullable=False),
        sa.Column("condition_type", achievement_condition_type, nullable=False),
        sa.Column("condition_value", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "daily_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("anxiety_level", sa.Integer(), nullable=False),
        sa.Column("emotions", sa.JSON(), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("ai_analysis", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_daily_entries_user_id_date",
        "daily_entries",
        ["user_id", "date"],
        unique=False,
    )

    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("dark_mode", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "notifications_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="ru"),
        sa.Column("daily_reminder_time", sa.String(length=5), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "user_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_tasks_user_id_completed_at",
        "user_tasks",
        ["user_id", "completed_at"],
        unique=False,
    )

    op.create_table(
        "user_achievements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("achievement_id", sa.Integer(), nullable=False),
        sa.Column("earned_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["achievement_id"], ["achievements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )


def downgrade():
    op.drop_table("user_achievements")
    op.drop_index("ix_user_tasks_user_id_completed_at", table_name="user_tasks")
    op.drop_table("user_tasks")
    op.drop_table("user_settings")
    op.drop_index("ix_daily_entries_user_id_date", table_name="daily_entries")
    op.drop_table("daily_entries")
    op.drop_table("achievements")
    op.drop_table("tasks")
    op.drop_table("users")
    achievement_condition_type.drop(op.get_bind(), checkfirst=True)
    task_difficulty.drop(op.get_bind(), checkfirst=True)
