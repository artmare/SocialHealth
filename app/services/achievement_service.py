from datetime import datetime, timezone

import sqlalchemy as sa

from app.extensions import db
from app.models import Achievement, DailyEntry, User, UserAchievement, UserTask


ACHIEVEMENTS = [
    {
        "name": "First entry",
        "description": "Create your first diary entry.",
        "icon": "📝",
        "condition_type": "total_entries",
        "condition_value": 1,
    },
    {
        "name": "Reflective week",
        "description": "Create 7 diary entries.",
        "icon": "📔",
        "condition_type": "total_entries",
        "condition_value": 7,
    },
    {
        "name": "First step",
        "description": "Complete your first CBT task.",
        "icon": "✅",
        "condition_type": "tasks_completed",
        "condition_value": 1,
    },
    {
        "name": "Practice builder",
        "description": "Complete 10 CBT tasks.",
        "icon": "🌱",
        "condition_type": "tasks_completed",
        "condition_value": 10,
    },
    {
        "name": "Three-day streak",
        "description": "Keep a 3-day activity streak.",
        "icon": "🔥",
        "condition_type": "streak",
        "condition_value": 3,
    },
    {
        "name": "Level 3",
        "description": "Reach level 3.",
        "icon": "⭐",
        "condition_type": "level_reached",
        "condition_value": 3,
    },
    {
        "name": "500 XP",
        "description": "Earn 500 total XP.",
        "icon": "🏅",
        "condition_type": "xp_earned",
        "condition_value": 500,
    },
]


def seed_achievements() -> int:
    for data in ACHIEVEMENTS:
        achievement = db.session.execute(
            sa.select(Achievement).where(Achievement.name == data["name"])
        ).scalar_one_or_none()
        if achievement:
            for key, value in data.items():
                setattr(achievement, key, value)
        else:
            db.session.add(Achievement(**data))
    db.session.commit()
    return db.session.scalar(sa.select(sa.func.count(Achievement.id))) or 0


class AchievementService:
    @staticmethod
    def _metric(user: User, condition_type: str) -> int:
        if condition_type == "streak":
            return user.streak
        if condition_type == "level_reached":
            return user.level
        if condition_type == "xp_earned":
            return user.xp
        if condition_type == "total_entries":
            return db.session.scalar(
                sa.select(sa.func.count(DailyEntry.id)).where(
                    DailyEntry.user_id == user.id
                )
            ) or 0
        if condition_type == "tasks_completed":
            return db.session.scalar(
                sa.select(sa.func.count(UserTask.id)).where(
                    UserTask.user_id == user.id,
                    UserTask.completed == True,
                )
            ) or 0
        return 0

    @staticmethod
    def award_for_user(user_id: int) -> list[Achievement]:
        user = db.session.get(User, user_id)
        if user is None:
            return []

        if not db.session.scalar(sa.select(sa.func.count(Achievement.id))):
            seed_achievements()

        earned_ids = set(
            db.session.execute(
                sa.select(UserAchievement.achievement_id).where(
                    UserAchievement.user_id == user_id
                )
            ).scalars()
        )

        newly_earned: list[Achievement] = []
        achievements = db.session.execute(sa.select(Achievement)).scalars().all()
        for achievement in achievements:
            if achievement.id in earned_ids:
                continue
            value = AchievementService._metric(user, achievement.condition_type)
            if value >= achievement.condition_value:
                db.session.add(
                    UserAchievement(
                        user_id=user_id,
                        achievement_id=achievement.id,
                        earned_at=datetime.now(timezone.utc),
                    )
                )
                newly_earned.append(achievement)

        if newly_earned:
            db.session.commit()
        return newly_earned
