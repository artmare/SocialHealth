"""
seed_tasks.py — наполнение БД 30 CBT-заданиями для социальной тревожности.
Каждое задание имеет русскую и английскую версию (title/description + title_en/description_en).
Запуск: python seed_tasks.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models import Task
from app.services.achievement_service import seed_achievements


TASKS = [
    # =============== EASY (anxiety 1-3, xp=10) ===============
    {
        "title": "Дыхание 4-7-8",
        "title_en": "4-7-8 Breathing",
        "description": (
            "Выполните 5 циклов дыхания по технике 4-7-8: "
            "вдох через нос на 4 счёта, задержка дыхания на 7 счётов, "
            "медленный выдох через рот на 8 счётов. Это активирует "
            "парасимпатическую нервную систему и снижает тревогу."
        ),
        "description_en": (
            "Do 5 cycles of 4-7-8 breathing: inhale through the nose "
            "for 4 counts, hold for 7 counts, slowly exhale through the "
            "mouth for 8 counts. This activates the parasympathetic "
            "nervous system and reduces anxiety."
        ),
        "difficulty": "easy", "xp_reward": 10, "category": "breathing",
        "min_anxiety": 1, "max_anxiety": 3,
    },
    {
        "title": "Три хороших момента",
        "title_en": "Three Good Moments",
        "description": (
            "Запишите в дневнике 3 позитивных момента за сегодня. "
            "Это могут быть мелочи: вкусный кофе, тёплый солнечный луч, "
            "улыбка прохожего. Практика благодарности смещает фокус "
            "с негативных мыслей к позитивным."
        ),
        "description_en": (
            "Write down 3 positive moments from today in your journal. "
            "Tiny things count: tasty coffee, a warm sunbeam, a passerby's "
            "smile. Gratitude practice shifts your focus from negative "
            "to positive thoughts."
        ),
        "difficulty": "easy", "xp_reward": 10, "category": "writing",
        "min_anxiety": 1, "max_anxiety": 3,
    },
    {
        "title": "Наблюдатель",
        "title_en": "Observer",
        "description": (
            "Сядьте в кафе или парке на 10 минут и просто наблюдайте за "
            "людьми. Заметьте 5 разных эмоций, 5 жестов, 5 разговоров. "
            "Это упражнение тренирует присутствие в моменте и снижает "
            "самоосознанность."
        ),
        "description_en": (
            "Sit in a cafe or park for 10 minutes and just observe people. "
            "Notice 5 different emotions, 5 gestures, 5 conversations. "
            "This exercise trains presence in the moment and reduces "
            "self-consciousness."
        ),
        "difficulty": "easy", "xp_reward": 10, "category": "social",
        "min_anxiety": 1, "max_anxiety": 3,
    },
    {
        "title": "Прогрессивная релаксация",
        "title_en": "Progressive Relaxation",
        "description": (
            "Лягте удобно и последовательно напрягайте каждую группу мышц "
            "(стопы, икры, бёдра, живот, руки, плечи, лицо) на 5 секунд, "
            "затем расслабляйте на 10 секунд. Снимает физическое напряжение."
        ),
        "description_en": (
            "Lie down comfortably and sequentially tense each muscle group "
            "(feet, calves, thighs, abdomen, arms, shoulders, face) for "
            "5 seconds, then relax for 10 seconds. Releases physical tension."
        ),
        "difficulty": "easy", "xp_reward": 10, "category": "body",
        "min_anxiety": 1, "max_anxiety": 3,
    },
    {
        "title": "Дневник мыслей",
        "title_en": "Thought Diary",
        "description": (
            "Запишите 3 тревожные мысли за день. Для каждой ответьте: "
            "«Это факт или интерпретация?», «Какие доказательства за и против?», "
            "«Как бы я посоветовал другу в этой ситуации?»"
        ),
        "description_en": (
            "Write down 3 anxious thoughts from your day. For each, answer: "
            "\"Is this a fact or interpretation?\", \"What is the evidence "
            "for and against?\", \"How would I advise a friend in this situation?\""
        ),
        "difficulty": "easy", "xp_reward": 10, "category": "cognition",
        "min_anxiety": 1, "max_anxiety": 3,
    },
    {
        "title": "Медитация 5 минут",
        "title_en": "5-Minute Meditation",
        "description": (
            "Найдите тихое место и медитируйте 5 минут. Сосредоточьтесь "
            "на дыхании. Если мысли блуждают — мягко возвращайте внимание "
            "к дыханию. Не оценивайте себя."
        ),
        "description_en": (
            "Find a quiet spot and meditate for 5 minutes. Focus on your "
            "breath. When thoughts wander, gently bring attention back to "
            "the breath. Don't judge yourself."
        ),
        "difficulty": "easy", "xp_reward": 10, "category": "body",
        "min_anxiety": 1, "max_anxiety": 3,
    },
    {
        "title": "Сканирование тела",
        "title_en": "Body Scan",
        "description": (
            "Лягте и направляйте внимание от макушки до пяток, замечая "
            "ощущения в каждой части тела без оценки. Это упражнение "
            "усиливает осознанность и снижает соматические симптомы тревоги."
        ),
        "description_en": (
            "Lie down and direct your attention from head to heels, "
            "noticing sensations in each body part without judgment. "
            "This exercise enhances mindfulness and reduces somatic "
            "symptoms of anxiety."
        ),
        "difficulty": "easy", "xp_reward": 10, "category": "body",
        "min_anxiety": 1, "max_anxiety": 3,
    },
    {
        "title": "Письмо себе",
        "title_en": "Letter to Yourself",
        "description": (
            "Напишите письмо себе в будущее (через год). Опишите свои "
            "мечты, страхи, чего хотите достичь. Это упражнение помогает "
            "увидеть перспективу и снизить фокус на текущих тревогах."
        ),
        "description_en": (
            "Write a letter to your future self (one year from now). "
            "Describe your dreams, fears, what you want to achieve. "
            "This helps you see perspective and reduces focus on "
            "current worries."
        ),
        "difficulty": "easy", "xp_reward": 10, "category": "writing",
        "min_anxiety": 1, "max_anxiety": 3,
    },
    {
        "title": "Утренняя растяжка",
        "title_en": "Morning Stretch",
        "description": (
            "Сделайте 10-минутную растяжку сразу после пробуждения. "
            "Это снижает кортизол и улучшает настроение на весь день. "
            "Простые движения: наклоны, повороты, потягивания."
        ),
        "description_en": (
            "Do a 10-minute stretch right after waking up. This lowers "
            "cortisol and improves mood for the whole day. Simple moves: "
            "bends, twists, full-body stretches."
        ),
        "difficulty": "easy", "xp_reward": 10, "category": "body",
        "min_anxiety": 1, "max_anxiety": 3,
    },
    {
        "title": "Музыкальная пауза",
        "title_en": "Music Break",
        "description": (
            "Послушайте 10 минут любимой расслабляющей музыки с закрытыми "
            "глазами. Фокусируйтесь только на звуке. Музыка снижает уровень "
            "стрессовых гормонов."
        ),
        "description_en": (
            "Listen to 10 minutes of your favourite relaxing music with "
            "closed eyes. Focus only on the sound. Music reduces levels "
            "of stress hormones."
        ),
        "difficulty": "easy", "xp_reward": 10, "category": "body",
        "min_anxiety": 1, "max_anxiety": 3,
    },
    # =============== MEDIUM (anxiety 4-6, xp=25) ===============
    {
        "title": "Первый шаг",
        "title_en": "First Step",
        "description": (
            "Поздоровайтесь с одним новым человеком сегодня (продавец, "
            "сосед, коллега). Используйте имя, если знаете. Минимум — "
            "контакт глазами и улыбка. Это разрушает социальный барьер."
        ),
        "description_en": (
            "Say hello to one new person today (cashier, neighbor, "
            "coworker). Use their name if you know it. The minimum is "
            "eye contact and a smile. This breaks the social barrier."
        ),
        "difficulty": "medium", "xp_reward": 25, "category": "social",
        "min_anxiety": 4, "max_anxiety": 6,
    },
    {
        "title": "Вопрос незнакомцу",
        "title_en": "Question to a Stranger",
        "description": (
            "Задайте простой вопрос незнакомцу: «Который час?», «Где "
            "ближайшая аптека?», «Как доехать до...?». Это упражнение "
            "тренирует инициацию разговора в безопасной форме."
        ),
        "description_en": (
            "Ask a simple question to a stranger: \"What time is it?\", "
            "\"Where's the nearest pharmacy?\", \"How do I get to...?\". "
            "This trains conversation initiation in a safe format."
        ),
        "difficulty": "medium", "xp_reward": 25, "category": "social",
        "min_anxiety": 4, "max_anxiety": 6,
    },
    {
        "title": "Комплимент",
        "title_en": "Compliment",
        "description": (
            "Сделайте искренний комплимент одному человеку сегодня. "
            "Не про внешность — про действие или качество: «У тебя "
            "классное решение», «Спасибо за помощь»."
        ),
        "description_en": (
            "Give one sincere compliment to someone today. Not about "
            "appearance — about an action or quality: \"That's a great "
            "solution\", \"Thanks for the help\"."
        ),
        "difficulty": "medium", "xp_reward": 25, "category": "social",
        "min_anxiety": 4, "max_anxiety": 6,
    },
    {
        "title": "Маленькая покупка",
        "title_en": "Small Purchase",
        "description": (
            "Сходите в магазин и купите что-то, что требует обращения к "
            "продавцу (а не self-checkout). Уточните детали: «Есть ли "
            "ваш размер?», «Что посоветуете?»."
        ),
        "description_en": (
            "Go to a store and buy something that requires speaking to "
            "a clerk (not self-checkout). Ask for details: \"Do you have "
            "my size?\", \"What would you recommend?\""
        ),
        "difficulty": "medium", "xp_reward": 25, "category": "social",
        "min_anxiety": 4, "max_anxiety": 6,
    },
    {
        "title": "Телефонный звонок",
        "title_en": "Phone Call",
        "description": (
            "Позвоните в какое-то учреждение (банк, поликлиника, "
            "магазин) и задайте конкретный вопрос. Многим тревожно "
            "звонить по телефону — это упражнение преодолевает страх."
        ),
        "description_en": (
            "Call some institution (bank, clinic, store) and ask a "
            "specific question. Many people are anxious about phone "
            "calls — this exercise overcomes that fear."
        ),
        "difficulty": "medium", "xp_reward": 25, "category": "social",
        "min_anxiety": 4, "max_anxiety": 6,
    },
    {
        "title": "Чек-ин в кафе",
        "title_en": "Cafe Check-in",
        "description": (
            "Зайдите в кафе один, закажите что-то у бариста, сядьте за "
            "столик и проведите 20 минут (читая или просто наблюдая). "
            "Без телефона. Это тренирует комфорт в социальном пространстве."
        ),
        "description_en": (
            "Go to a cafe alone, order from the barista, sit at a table "
            "and spend 20 minutes (reading or just watching). No phone. "
            "This builds comfort in social spaces."
        ),
        "difficulty": "medium", "xp_reward": 25, "category": "social",
        "min_anxiety": 4, "max_anxiety": 6,
    },
    {
        "title": "Позитивное предсказание",
        "title_en": "Positive Prediction",
        "description": (
            "Запишите тревожный сценарий и рядом — реалистичный позитивный. "
            "Например: «Я провалю презентацию» → «Я подготовился, поэтому "
            "всё пройдёт нормально». Тренируется когнитивная гибкость."
        ),
        "description_en": (
            "Write down an anxious scenario and next to it — a realistic "
            "positive one. E.g.: \"I'll fail the presentation\" → \"I'm "
            "prepared, so it'll go fine\". Trains cognitive flexibility."
        ),
        "difficulty": "medium", "xp_reward": 25, "category": "cognition",
        "min_anxiety": 4, "max_anxiety": 6,
    },
    {
        "title": "Мини-презентация",
        "title_en": "Mini-presentation",
        "description": (
            "Расскажите 1 близкому человеку что-то интересное за 3-5 минут "
            "(книга, фильм, идея). Это безопасная подготовка к публичным "
            "выступлениям."
        ),
        "description_en": (
            "Tell one close person something interesting for 3-5 minutes "
            "(a book, film, idea). This is safe practice for public "
            "speaking."
        ),
        "difficulty": "medium", "xp_reward": 25, "category": "social",
        "min_anxiety": 4, "max_anxiety": 6,
    },
    {
        "title": "Групповое сообщение",
        "title_en": "Group Message",
        "description": (
            "Напишите в чат, где вас много, сообщение по теме (не личное "
            "общение). Например, поделитесь полезной ссылкой или "
            "поздравьте кого-то с днём рождения."
        ),
        "description_en": (
            "Post in a group chat with many people — something on-topic "
            "(not private). For example, share a useful link or wish "
            "someone a happy birthday."
        ),
        "difficulty": "medium", "xp_reward": 25, "category": "social",
        "min_anxiety": 4, "max_anxiety": 6,
    },
    {
        "title": "Самораскрытие",
        "title_en": "Self-disclosure",
        "description": (
            "Расскажите близкому человеку 1 личную деталь о себе, "
            "которую обычно не делитесь (страх, мечта, неудача). "
            "Уязвимость укрепляет связи."
        ),
        "description_en": (
            "Tell a close person one personal detail about yourself "
            "that you usually keep private (a fear, dream, failure). "
            "Vulnerability deepens connections."
        ),
        "difficulty": "medium", "xp_reward": 25, "category": "social",
        "min_anxiety": 4, "max_anxiety": 6,
    },
    # =============== HARD (anxiety 7-10, xp=50) ===============
    {
        "title": "Инициатор",
        "title_en": "Initiator",
        "description": (
            "Предложите конкретный план встречи или активности 2-3 людям. "
            "«Пойдёмте в кино в пятницу?», «Кто хочет на пробежку утром?». "
            "Это шаг от пассивности к активной социальной роли."
        ),
        "description_en": (
            "Propose a concrete plan for a meetup or activity to 2-3 "
            "people. \"Movie on Friday?\", \"Anyone want to go for a "
            "morning run?\". A step from passivity to active social role."
        ),
        "difficulty": "hard", "xp_reward": 50, "category": "social",
        "min_anxiety": 7, "max_anxiety": 10,
    },
    {
        "title": "Публичное слово",
        "title_en": "Speak Up Publicly",
        "description": (
            "Высказывайтесь на встрече/уроке/собрании. Задайте вопрос или "
            "сделайте комментарий. Минимум — 2 высказывания. Это разрушает "
            "паттерн избегания публичной речи."
        ),
        "description_en": (
            "Speak up in a meeting / class / gathering. Ask a question "
            "or make a comment. At least 2 contributions. This breaks "
            "the public-speech avoidance pattern."
        ),
        "difficulty": "hard", "xp_reward": 50, "category": "social",
        "min_anxiety": 7, "max_anxiety": 10,
    },
    {
        "title": "Отказ",
        "title_en": "Saying No",
        "description": (
            "Откажите кому-то в просьбе, которая вам неудобна. Не "
            "оправдывайтесь излишне — «Спасибо, но я не могу». Это "
            "тренирует ассертивность и личные границы."
        ),
        "description_en": (
            "Decline a request that makes you uncomfortable. Don't "
            "over-justify — \"Thanks, but I can't.\" This trains "
            "assertiveness and personal boundaries."
        ),
        "difficulty": "hard", "xp_reward": 50, "category": "social",
        "min_anxiety": 7, "max_anxiety": 10,
    },
    {
        "title": "Вечеринка или митап",
        "title_en": "Party or Meetup",
        "description": (
            "Сходите на вечеринку или митап (хобби, профессиональный). "
            "Цель — поговорить с 3 новыми людьми минимум 5 минут с "
            "каждым. Используйте «small talk» техники."
        ),
        "description_en": (
            "Go to a party or meetup (hobby or professional). Goal: "
            "talk to 3 new people for at least 5 minutes each. Use "
            "small-talk techniques."
        ),
        "difficulty": "hard", "xp_reward": 50, "category": "social",
        "min_anxiety": 7, "max_anxiety": 10,
    },
    {
        "title": "Помощь незнакомцу",
        "title_en": "Help a Stranger",
        "description": (
            "Подойдите к незнакомцу, который выглядит растерянным "
            "(потерял дорогу, не понимает таблицу), и предложите помощь. "
            "Альтруизм снижает социальную тревогу."
        ),
        "description_en": (
            "Approach a stranger who looks lost (asking for directions, "
            "confused by a schedule) and offer help. Altruism reduces "
            "social anxiety."
        ),
        "difficulty": "hard", "xp_reward": 50, "category": "social",
        "min_anxiety": 7, "max_anxiety": 10,
    },
    {
        "title": "Селфи с незнакомцем",
        "title_en": "Selfie with a Stranger",
        "description": (
            "Попросите незнакомца сфотографировать вас (или сделайте "
            "селфи вместе по теме). Это упражнение из expoзure-терапии "
            "для преодоления страха внимания."
        ),
        "description_en": (
            "Ask a stranger to take a photo of you (or take a selfie "
            "together on some pretext). This is an exposure-therapy "
            "exercise to overcome the fear of attention."
        ),
        "difficulty": "hard", "xp_reward": 50, "category": "social",
        "min_anxiety": 7, "max_anxiety": 10,
    },
    {
        "title": "Секунда смеха",
        "title_en": "A Second of Laughter",
        "description": (
            "В общественном месте (в очереди, в транспорте) расскажите "
            "анекдот или сделайте короткое забавное замечание. Если никто "
            "не засмеётся — заметьте, что мир не рухнул. Цель — "
            "пережить «провал» и убедиться, что это терпимо."
        ),
        "description_en": (
            "In a public place (queue, transit) tell a joke or make a "
            "short funny remark. If no one laughs — notice that the world "
            "didn't end. The goal is to live through a \"flop\" and see "
            "that it's tolerable."
        ),
        "difficulty": "hard", "xp_reward": 50, "category": "social",
        "min_anxiety": 7, "max_anxiety": 10,
    },
    {
        "title": "Совместный обед",
        "title_en": "Shared Lunch",
        "description": (
            "Пригласите коллегу или однокурсника на обед/кофе. "
            "Планируйте 3 темы для разговора заранее. Это инициация "
            "более глубокого социального контакта."
        ),
        "description_en": (
            "Invite a colleague or classmate to lunch/coffee. Plan "
            "3 conversation topics ahead. This initiates a deeper "
            "social connection."
        ),
        "difficulty": "hard", "xp_reward": 50, "category": "social",
        "min_anxiety": 7, "max_anxiety": 10,
    },
    {
        "title": "Импровизация",
        "title_en": "Improvisation",
        "description": (
            "Запишите 30-секундное видео, где рассказываете о себе, "
            "или примите участие в импровизационной игре. Это тренирует "
            "толерантность к неопределённости и неожиданным ситуациям."
        ),
        "description_en": (
            "Record a 30-second video about yourself, or take part in "
            "an improv game. This trains tolerance for uncertainty and "
            "unexpected situations."
        ),
        "difficulty": "hard", "xp_reward": 50, "category": "social",
        "min_anxiety": 7, "max_anxiety": 10,
    },
    {
        "title": "Профессиональная встреча",
        "title_en": "Professional Meeting",
        "description": (
            "Договоритесь о 30-минутной встрече с интересным вам "
            "профессионалом (наставник, коллега, эксперт). Подготовьте "
            "5 вопросов. Это формирует профессиональную сеть."
        ),
        "description_en": (
            "Arrange a 30-minute meeting with a professional you "
            "find interesting (mentor, colleague, expert). Prepare "
            "5 questions. This builds your professional network."
        ),
        "difficulty": "hard", "xp_reward": 50, "category": "social",
        "min_anxiety": 7, "max_anxiety": 10,
    },
]


def seed(app=None):
    if app is None:
        app = create_app("development")
    with app.app_context():
        for data in TASKS:
            t = Task.query.filter_by(title=data["title"]).first()
            if t:
                for key, value in data.items():
                    setattr(t, key, value)
            else:
                t = Task(**data)
                db.session.add(t)
        db.session.commit()
        seed_achievements()
        total = Task.query.count()
        return total


if __name__ == "__main__":
    app = create_app("development")
    n = seed(app)
    try:
        print(f"Seeded. Total tasks in DB: {n}")
    except UnicodeEncodeError:
        pass
