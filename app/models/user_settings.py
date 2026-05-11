from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Boolean, Time, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.user import User


class UserSettings(db.Model):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    dark_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    language: Mapped[str] = mapped_column(String(10), default="ru", nullable=False)
    daily_reminder_time: Mapped[str | None] = mapped_column(
        String(5), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="settings")
