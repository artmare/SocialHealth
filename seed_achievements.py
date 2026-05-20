from app import create_app
from app.services.achievement_service import seed_achievements


if __name__ == "__main__":
    app = create_app("development")
    with app.app_context():
        total = seed_achievements()
        print(f"Seeded achievements. Total achievements in DB: {total}")
