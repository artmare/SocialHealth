# SocialHealth

Веб-приложение для преодоления социальной тревожности с использованием
когнитивно-поведенческой терапии (CBT) и AI-анализа.

## Возможности

- Ежедневная оценка тревоги с AI-анализом (Claude API)
- 30+ CBT-заданий с системой XP и уровней
- Дашборд с графиками прогресса (Chart.js)
- SOS-режим при панической атаке (дыхание 4-7-8, заземление 5-4-3-2-1)
- Библиотека CBT-техник
- Профиль с достижениями и экспортом данных

## Стек

- **Backend:** Python 3.11 + Flask + SQLAlchemy
- **AI:** Anthropic Claude API
- **Frontend:** HTML5 / CSS3 / Vanilla JS / Chart.js
- **Auth:** JWT (Flask-JWT-Extended)
- **DB:** SQLite (dev) / PostgreSQL (prod)
- **Deploy:** Vercel

## Установка

```bash
git clone https://github.com/<user>/SocialHealth.git
cd SocialHealth
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # и заполните переменные
flask db upgrade            # миграции (или python -c "from app import create_app; from app.extensions import db; app=create_app('development'); ctx=app.app_context(); ctx.push(); db.create_all()")
python seed_tasks.py        # 30 CBT-заданий
flask run
```

## Тесты

```bash
pytest tests/ -v
```

Тесты используют SQLite in-memory и mock для AI — реальный API ключ не нужен.

## Мультиязычность

Интерфейс использует Flask-Babel. Поддерживаемые языки: `en`, `ru`, `uk`.
Подробная инструкция по обновлению переводов находится в `I18N.md`.

Основные команды:

```bash
python scripts/i18n.py extract
python scripts/i18n.py update
python scripts/i18n.py compile
python scripts/i18n.py check
```

## Деплой

Автоматический через GitHub Actions при push в `main`. Workflow:

1. **test** — устанавливает зависимости и прогоняет `pytest`

Production deploy runs on Vercel. See `VERCEL.md` for the required environment
variables and database setup.

## Структура

```
app/
├── routes/        # Blueprint'ы: auth, diary, tasks, dashboard, progress, api, sos, profile, tips, main
├── services/      # AIService, TaskService, StatsService
├── models/        # SQLAlchemy: User, DailyEntry, Task, UserTask, Achievement, UserAchievement, UserSettings
├── templates/     # Jinja2
├── static/        # CSS / JS
└── data/          # Статические данные (tips_data.py)
tests/             # pytest
```

## Дисклеймер

SocialHealth **не является медицинским сервисом**. При серьёзных проблемах
обращайтесь к специалисту. Для психологической поддержки используйте **116 123**.
В экстренных случаях — **112**.
