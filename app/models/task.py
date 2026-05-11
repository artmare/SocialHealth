from typing import List

from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Task(db.Model):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    difficulty: Mapped[str] = mapped_column(
        Enum("easy", "medium", "hard", name="task_difficulty"),
        nullable=False,
    )
    xp_reward: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    min_anxiety: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_anxiety: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    user_tasks: Mapped[List["UserTask"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
