from typing import List

from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Achievement(db.Model):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    icon: Mapped[str] = mapped_column(String(10), nullable=False)
    condition_type: Mapped[str] = mapped_column(
        Enum(
            "streak",
            "total_entries",
            "tasks_completed",
            "level_reached",
            "xp_earned",
            name="achievement_condition_type",
        ),
        nullable=False,
    )
    condition_value: Mapped[int] = mapped_column(Integer, nullable=False)

    user_achievements: Mapped[List["UserAchievement"]] = relationship(
        back_populates="achievement", cascade="all, delete-orphan"
    )
