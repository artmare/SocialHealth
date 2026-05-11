from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, Index, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.user import User


class DailyEntry(db.Model):
    __tablename__ = "daily_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    anxiety_level: Mapped[int] = mapped_column(Integer, nullable=False)
    emotions: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_analysis: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="entries")

    __table_args__ = (
        Index("ix_daily_entries_user_id_date", "user_id", "date"),
    )
