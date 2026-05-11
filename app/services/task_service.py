from datetime import date, datetime, timezone, timedelta

import sqlalchemy as sa

from app.extensions import db
from app.models import Task, UserTask, User, DailyEntry


class TaskService:
    @staticmethod
    def get_difficulty_for_anxiety(anxiety_level: int) -> str:
        if anxiety_level <= 3:
            return "easy"
        elif anxiety_level <= 6:
            return "medium"
        return "hard"

    @staticmethod
    def get_daily_task(user_id: int, anxiety_level: int) -> Task | None:
        difficulty = TaskService.get_difficulty_for_anxiety(anxiety_level)

        # task IDs that user already completed
        completed_ids = db.session.execute(
            sa.select(UserTask.task_id).where(
                UserTask.user_id == user_id,
                UserTask.completed == True,
            )
        ).scalars().all()

        if completed_ids:
            task = db.session.execute(
                sa.select(Task)
                .where(Task.difficulty == difficulty)
                .where(Task.id.notin_(completed_ids))
                .order_by(sa.func.random())
                .limit(1)
            ).scalar_one_or_none()
        else:
            task = db.session.execute(
                sa.select(Task)
                .where(Task.difficulty == difficulty)
                .order_by(sa.func.random())
                .limit(1)
            ).scalar_one_or_none()

        if not task:
            # All tasks of this difficulty completed — cycle back
            task = db.session.execute(
                sa.select(Task)
                .where(Task.difficulty == difficulty)
                .order_by(sa.func.random())
                .limit(1)
            ).scalar_one_or_none()

        return task

    @staticmethod
    def assign_task(user_id: int, task_id: int) -> UserTask:
        existing = db.session.execute(
            sa.select(UserTask).where(
                UserTask.user_id == user_id,
                UserTask.task_id == task_id,
            )
        ).scalar_one_or_none()

        if existing:
            return existing

        ut = UserTask(
            user_id=user_id,
            task_id=task_id,
            completed=False,
        )
        db.session.add(ut)
        db.session.commit()
        return ut

    @staticmethod
    def complete_task(user_id: int, task_id: int, feedback: str | None = None) -> dict:
        user = db.session.execute(
            sa.select(User).where(User.id == user_id)
        ).scalar_one()

        task = db.session.execute(
            sa.select(Task).where(Task.id == task_id)
        ).scalar_one()

        # Find or create UserTask
        ut = db.session.execute(
            sa.select(UserTask).where(
                UserTask.user_id == user_id,
                UserTask.task_id == task_id,
            )
        ).scalar_one_or_none()

        if ut is None:
            ut = UserTask(user_id=user_id, task_id=task_id, completed=False)
            db.session.add(ut)
            db.session.commit()

        # Avoid double XP if already completed
        already_completed = ut.completed
        if not already_completed:
            ut.completed = True
            ut.completed_at = datetime.now(timezone.utc)
            if feedback:
                ut.feedback = feedback

            leveled_up = user.add_xp(task.xp_reward)

            # Update streak
            today = date.today()
            if user.last_activity_date == today:
                pass  # streak unchanged
            elif user.last_activity_date == today - timedelta(days=1):
                user.streak += 1
            else:
                user.streak = 1

            if user.streak > user.longest_streak:
                user.longest_streak = user.streak
            user.last_activity_date = today

            db.session.commit()
        else:
            if feedback and not ut.feedback:
                ut.feedback = feedback
                db.session.commit()
            leveled_up = False

        return {
            "xp_earned": task.xp_reward if not already_completed else 0,
            "leveled_up": leveled_up,
            "new_level": user.level,
            "total_xp": user.xp,
            "streak": user.streak,
        }

    @staticmethod
    def get_user_task_history(user_id: int, page: int = 1, per_page: int = 10) -> dict:
        total = db.session.scalar(
            sa.select(sa.func.count(UserTask.id)).where(UserTask.user_id == user_id)
        )

        tasks = db.session.execute(
            sa.select(UserTask)
            .where(UserTask.user_id == user_id)
            .order_by(UserTask.completed.asc(), UserTask.assigned_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        ).scalars().all()

        total_pages = (total + per_page - 1) // per_page if total else 1

        return {
            "tasks": tasks,
            "total": total,
            "page": page,
            "pages": total_pages,
        }

    @staticmethod
    def get_last_anxiety_level(user_id: int) -> int:
        entry = db.session.execute(
            sa.select(DailyEntry)
            .where(DailyEntry.user_id == user_id)
            .order_by(DailyEntry.date.desc(), DailyEntry.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        return entry.anxiety_level if entry else 5
