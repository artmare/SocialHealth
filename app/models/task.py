from typing import List

from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Task(db.Model):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Базовые поля (используются как fallback). По историческим причинам — на русском.
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    # Английские версии (могут быть None у старых записей)
    title_en: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description_en: Mapped[str | None] = mapped_column(String(1000), nullable=True)
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

    # ---------- Локализованные геттеры ----------

    @staticmethod
    def _current_locale() -> str:
        try:
            from flask import g, has_request_context
            if has_request_context():
                loc = getattr(g, "locale", None)
                if loc in ("en", "ru", "uk"):
                    return loc
        except Exception:
            pass
        return "en"

    @property
    def localized_title(self) -> str:
        if self._current_locale() == "uk":
            from app.task_i18n import ukrainian_task_text
            text = ukrainian_task_text(self.title_en)
            if text:
                return text[0]
        if self._current_locale() == "en" and self.title_en:
            return self.title_en
        return self.title

    @property
    def localized_description(self) -> str | None:
        if self._current_locale() == "uk":
            from app.task_i18n import ukrainian_task_text
            text = ukrainian_task_text(self.title_en)
            if text:
                return text[1]
        if self._current_locale() == "en" and self.description_en:
            return self.description_en
        return self.description
