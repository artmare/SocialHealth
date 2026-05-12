from datetime import date, datetime, timedelta, timezone

import sqlalchemy as sa

from app.extensions import db
from app.models import (
    DailyEntry,
    User,
    UserTask,
    Task,
    Achievement,
    UserAchievement,
)
from config import BaseConfig


class StatsService:
    @staticmethod
    def get_dashboard_stats(user_id: int) -> dict:
        user = db.session.execute(
            sa.select(User).where(User.id == user_id)
        ).scalar_one()

        total_tasks_completed = db.session.scalar(
            sa.select(sa.func.count(UserTask.id)).where(
                UserTask.user_id == user_id,
                UserTask.completed == True,
            )
        ) or 0

        total_entries = db.session.scalar(
            sa.select(sa.func.count(DailyEntry.id)).where(
                DailyEntry.user_id == user_id
            )
        ) or 0

        avg_anxiety = db.session.scalar(
            sa.select(sa.func.avg(DailyEntry.anxiety_level)).where(
                DailyEntry.user_id == user_id
            )
        )
        avg_anxiety = round(float(avg_anxiety), 2) if avg_anxiety is not None else 0.0

        week_ago = date.today() - timedelta(days=7)
        avg_anxiety_week = db.session.scalar(
            sa.select(sa.func.avg(DailyEntry.anxiety_level)).where(
                DailyEntry.user_id == user_id,
                DailyEntry.date >= week_ago,
            )
        )
        avg_anxiety_week = (
            round(float(avg_anxiety_week), 2) if avg_anxiety_week is not None else 0.0
        )

        levels = BaseConfig.XP_LEVELS
        titles = BaseConfig.LEVEL_TITLES
        max_level = len(levels)

        level = user.level
        if level < 1:
            level = 1
        if level > max_level:
            level = max_level

        level_title = titles[level - 1] if 1 <= level <= len(titles) else titles[-1]

        if level >= max_level:
            xp_to_next_level = 0
            xp_progress_pct = 100.0
        else:
            current_threshold = levels[level - 1]
            next_threshold = levels[level]
            span = next_threshold - current_threshold
            progress = max(0, user.xp - current_threshold)
            xp_to_next_level = max(0, next_threshold - user.xp)
            xp_progress_pct = round((progress / span) * 100, 2) if span > 0 else 100.0
            if xp_progress_pct > 100:
                xp_progress_pct = 100.0

        return {
            "streak": user.streak,
            "xp": user.xp,
            "level": level,
            "level_title": level_title,
            "total_tasks_completed": total_tasks_completed,
            "total_entries": total_entries,
            "avg_anxiety": avg_anxiety,
            "avg_anxiety_week": avg_anxiety_week,
            "xp_to_next_level": xp_to_next_level,
            "xp_progress_pct": xp_progress_pct,
        }

    @staticmethod
    def get_anxiety_history(user_id: int, days: int = 30) -> list[dict]:
        since = date.today() - timedelta(days=days)

        rows = db.session.execute(
            sa.select(DailyEntry.date, DailyEntry.anxiety_level)
            .where(
                DailyEntry.user_id == user_id,
                DailyEntry.date >= since,
            )
            .order_by(DailyEntry.date.asc(), DailyEntry.created_at.asc())
        ).all()

        # If multiple entries on same day, keep last one (latest created_at).
        by_date: dict[date, int] = {}
        for d, lvl in rows:
            by_date[d] = lvl

        return [
            {"date": d.isoformat(), "anxiety_level": lvl}
            for d, lvl in sorted(by_date.items())
        ]

    @staticmethod
    def get_tasks_by_week(user_id: int, weeks: int = 8) -> list[dict]:
        today = date.today()
        # Start of current week (Monday)
        current_monday = today - timedelta(days=today.weekday())
        start_monday = current_monday - timedelta(weeks=weeks - 1)
        start_dt = datetime.combine(start_monday, datetime.min.time(), tzinfo=timezone.utc)

        rows = db.session.execute(
            sa.select(UserTask.completed_at).where(
                UserTask.user_id == user_id,
                UserTask.completed == True,
                UserTask.completed_at.isnot(None),
                UserTask.completed_at >= start_dt,
            )
        ).all()

        buckets: dict[date, int] = {}
        for i in range(weeks):
            buckets[start_monday + timedelta(weeks=i)] = 0

        for (completed_at,) in rows:
            d = completed_at.date()
            monday = d - timedelta(days=d.weekday())
            if monday in buckets:
                buckets[monday] += 1

        return [
            {"week": monday.isoformat(), "count": count}
            for monday, count in sorted(buckets.items())
        ]

    @staticmethod
    def get_recent_entries(user_id: int, limit: int = 5) -> list[DailyEntry]:
        return db.session.execute(
            sa.select(DailyEntry)
            .where(DailyEntry.user_id == user_id)
            .order_by(DailyEntry.date.desc(), DailyEntry.created_at.desc())
            .limit(limit)
        ).scalars().all()

    @staticmethod
    def get_anxiety_comparison(user_id: int) -> dict:
        today = date.today()
        current_start = today - timedelta(days=6)  # last 7 days incl. today
        previous_start = today - timedelta(days=13)
        previous_end = today - timedelta(days=7)

        current_avg = db.session.scalar(
            sa.select(sa.func.avg(DailyEntry.anxiety_level)).where(
                DailyEntry.user_id == user_id,
                DailyEntry.date >= current_start,
                DailyEntry.date <= today,
            )
        )
        previous_avg = db.session.scalar(
            sa.select(sa.func.avg(DailyEntry.anxiety_level)).where(
                DailyEntry.user_id == user_id,
                DailyEntry.date >= previous_start,
                DailyEntry.date <= previous_end,
            )
        )

        current_week_avg = (
            round(float(current_avg), 2) if current_avg is not None else 0.0
        )
        previous_week_avg = (
            round(float(previous_avg), 2) if previous_avg is not None else 0.0
        )

        if current_avg is None or previous_avg is None or previous_week_avg == 0:
            change_pct = 0.0
            trend = "stable"
        else:
            # negative change_pct = anxiety went down = improvement
            change_pct = round(
                ((current_week_avg - previous_week_avg) / previous_week_avg) * 100, 1
            )
            if change_pct <= -5:
                trend = "improving"
            elif change_pct >= 5:
                trend = "worsening"
            else:
                trend = "stable"

        return {
            "current_week_avg": current_week_avg,
            "previous_week_avg": previous_week_avg,
            "change_pct": change_pct,
            "trend": trend,
        }

    @staticmethod
    def get_top_completed_tasks(user_id: int, limit: int = 5) -> list[UserTask]:
        return db.session.execute(
            sa.select(UserTask)
            .where(
                UserTask.user_id == user_id,
                UserTask.completed == True,
                UserTask.completed_at.isnot(None),
            )
            .order_by(UserTask.completed_at.desc())
            .limit(limit)
        ).scalars().all()

    @staticmethod
    def get_achievements_overview(user_id: int) -> list[dict]:
        all_achievements = db.session.execute(
            sa.select(Achievement).order_by(
                Achievement.condition_type, Achievement.condition_value
            )
        ).scalars().all()

        earned_map = {
            ua.achievement_id: ua
            for ua in db.session.execute(
                sa.select(UserAchievement).where(UserAchievement.user_id == user_id)
            ).scalars().all()
        }

        result = []
        for ach in all_achievements:
            ua = earned_map.get(ach.id)
            result.append(
                {
                    "id": ach.id,
                    "name": ach.name,
                    "description": ach.description,
                    "icon": ach.icon,
                    "condition_type": ach.condition_type,
                    "condition_value": ach.condition_value,
                    "earned": ua is not None,
                    "earned_at": ua.earned_at.isoformat() if ua else None,
                }
            )
        return result
