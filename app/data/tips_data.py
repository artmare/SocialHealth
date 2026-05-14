"""
Статические данные техник CBT для модуля 9 (/tips/).
Никаких БД — это справочник.

Структура: каждое поле существует в двух языках (поле и поле_en).
По умолчанию русские названия — потому что советы изначально писались
на русском. Геттеры get_tip_localized / localized_tips подменяют
поля английскими версиями, когда g.locale == 'en'.
"""

# ===================== категории и сложности =====================

CATEGORIES_BY_LOCALE = {
    "en": {
        "breathing": {"icon": "🫁", "name": "Breathing"},
        "cognition": {"icon": "🧠", "name": "Cognition"},
        "body":      {"icon": "🧘", "name": "Body"},
    },
    "ru": {
        "breathing": {"icon": "🫁", "name": "Дыхание"},
        "cognition": {"icon": "🧠", "name": "Когниция"},
        "body":      {"icon": "🧘", "name": "Тело"},
    },
}

DIFFICULTY_LABELS_BY_LOCALE = {
    "en": {"easy": "Easy", "medium": "Medium", "hard": "Hard"},
    "ru": {"easy": "Лёгкая", "medium": "Средняя", "hard": "Сложная"},
}

# Backward-compat (используется в импортах из app/routes/tips.py)
CATEGORIES = CATEGORIES_BY_LOCALE["ru"]
DIFFICULTY_LABELS = DIFFICULTY_LABELS_BY_LOCALE["ru"]


# ===================== техники =====================

TIPS = [
    # ============== BREATHING ==============
    {
        "id": 1,
        "slug": "breath-4-7-8",
        "category": "breathing",
        "icon": "🫁",
        "title": "Дыхание 4-7-8",
        "title_en": "4-7-8 Breathing",
        "summary": "Техника контролируемого дыхания для быстрого снижения тревоги",
        "summary_en": "Controlled breathing technique for fast anxiety relief",
        "description": (
            "Техника контролируемого дыхания, которая активирует "
            "парасимпатическую нервную систему и быстро снижает тревогу."
        ),
        "description_en": (
            "A controlled breathing technique that activates the "
            "parasympathetic nervous system and quickly reduces anxiety."
        ),
        "when_to_use": (
            "Перед важным разговором, при нарастающей тревоге, перед сном."
        ),
        "when_to_use_en": (
            "Before an important conversation, when anxiety rises, before sleep."
        ),
        "steps": [
            "Сядьте удобно, выпрямите спину.",
            "Закройте рот и вдохните через нос, считая до 4.",
            "Задержите дыхание, считая до 7.",
            "Медленно выдохните через рот со звуком, считая до 8.",
            "Это один цикл. Повторите 4 цикла.",
            "С практикой увеличивайте до 8 циклов.",
        ],
        "steps_en": [
            "Sit comfortably, straighten your back.",
            "Close your mouth and inhale through the nose, counting to 4.",
            "Hold your breath, counting to 7.",
            "Slowly exhale through the mouth with a sound, counting to 8.",
            "That is one cycle. Repeat 4 cycles.",
            "With practice increase to 8 cycles.",
        ],
        "duration": "5-10 мин",
        "duration_en": "5-10 min",
        "difficulty": "easy",
        "science": "Активирует блуждающий нерв, снижает ЧСС и кортизол.",
        "science_en": "Activates the vagus nerve, lowers heart rate and cortisol.",
        "interactive_url": "/sos/breathing",
        "interactive_label": "Попробовать с таймером",
        "interactive_label_en": "Try it with a timer",
    },
    {
        "id": 2,
        "slug": "diaphragmatic",
        "category": "breathing",
        "icon": "🫁",
        "title": "Диафрагмальное дыхание",
        "title_en": "Diaphragmatic Breathing",
        "summary": "Глубокое дыхание животом — снимает физические симптомы тревоги",
        "summary_en": "Deep belly breathing — relieves physical anxiety symptoms",
        "description": (
            "Глубокое дыхание животом, которое помогает при физических "
            "проявлениях тревоги — сердцебиении, потливости, дрожи."
        ),
        "description_en": (
            "Deep belly breathing that helps with physical anxiety symptoms — "
            "racing heart, sweating, trembling."
        ),
        "when_to_use": (
            "При физических симптомах тревоги: учащённое сердцебиение, "
            "потные ладони, дрожь."
        ),
        "when_to_use_en": (
            "When experiencing physical anxiety symptoms: racing heart, "
            "sweaty palms, trembling."
        ),
        "steps": [
            "Положите одну руку на грудь, другую на живот.",
            "Вдохните медленно через нос — живот должен подняться, а грудь остаться неподвижной.",
            "Задержите дыхание на 1-2 секунды.",
            "Медленно выдохните через рот — живот опускается.",
            "Повторяйте 5-10 минут.",
            "Следите, чтобы двигался именно живот, а не грудь.",
        ],
        "steps_en": [
            "Put one hand on your chest, the other on your belly.",
            "Inhale slowly through the nose — the belly should rise, the chest stay still.",
            "Hold your breath for 1-2 seconds.",
            "Exhale slowly through the mouth — the belly falls.",
            "Repeat for 5-10 minutes.",
            "Make sure the belly moves, not the chest.",
        ],
        "duration": "5-10 мин",
        "duration_en": "5-10 min",
        "difficulty": "easy",
        "science": None,
        "interactive_url": None,
    },
    {
        "id": 3,
        "slug": "box-breathing",
        "category": "breathing",
        "icon": "🫁",
        "title": "Квадратное дыхание (Box Breathing)",
        "title_en": "Box Breathing",
        "summary": "Техника спецназа: вдох-задержка-выдох-задержка по 4 секунды",
        "summary_en": "Used by special-ops: inhale-hold-exhale-hold for 4 seconds each",
        "description": (
            "Техника, которую используют спецназовцы для контроля стресса — "
            "вдох, задержка, выдох, задержка по 4 секунды."
        ),
        "description_en": (
            "A technique used by special forces to control stress — "
            "inhale, hold, exhale, hold for 4 seconds each."
        ),
        "when_to_use": (
            "Перед стрессовой ситуацией, когда нужна максимальная концентрация."
        ),
        "when_to_use_en": (
            "Before a stressful situation when maximum focus is needed."
        ),
        "steps": [
            "Вдохните через нос, считая до 4.",
            "Задержите дыхание на 4 счёта.",
            "Выдохните через рот на 4 счёта.",
            "Задержите дыхание на 4 счёта (с пустыми лёгкими).",
            "Повторите 4-6 циклов.",
        ],
        "steps_en": [
            "Inhale through the nose, counting to 4.",
            "Hold your breath for 4 counts.",
            "Exhale through the mouth for 4 counts.",
            "Hold your breath for 4 counts (with empty lungs).",
            "Repeat 4-6 cycles.",
        ],
        "duration": "3-5 мин",
        "duration_en": "3-5 min",
        "difficulty": "easy",
        "science": None,
        "interactive_url": None,
    },

    # ============== COGNITION ==============
    {
        "id": 4,
        "slug": "cognitive-restructuring",
        "category": "cognition",
        "icon": "🧠",
        "title": "Когнитивная реструктуризация",
        "title_en": "Cognitive Restructuring",
        "summary": "Замена автоматических негативных мыслей на реалистичные",
        "summary_en": "Replace automatic negative thoughts with realistic ones",
        "description": (
            "Ключевая техника CBT — выявление и замена автоматических "
            "негативных мыслей на более реалистичные."
        ),
        "description_en": (
            "The key CBT technique — identifying and replacing automatic "
            "negative thoughts with more realistic ones."
        ),
        "when_to_use": (
            "Когда ловите себя на мыслях: «все будут смеяться», "
            "«я обязательно провалюсь», «меня все осуждают»."
        ),
        "when_to_use_en": (
            "When you catch yourself thinking: \"everyone will laugh\", "
            "\"I'll definitely fail\", \"everyone judges me\"."
        ),
        "steps": [
            'Запишите тревожную мысль дословно (например: "Все будут смеяться надо мной").',
            "Определите когнитивное искажение:",
            {
                "text": "Виды искажений:",
                "sub": [
                    'Катастрофизация: "Всё будет ужасно".',
                    'Чтение мыслей: "Они думают, что я глупый".',
                    'Персонализация: "Это точно из-за меня".',
                    'Чёрно-белое мышление: "Либо идеально, либо провал".',
                ],
            },
            'Спросите себя: "Какие доказательства ЗА и ПРОТИВ этой мысли?"',
            "Напишите альтернативную, более реалистичную мысль.",
            "Оцените: как изменилась тревога (1-10)?",
        ],
        "steps_en": [
            'Write down the anxious thought word for word (e.g., "Everyone will laugh at me").',
            "Identify the cognitive distortion:",
            {
                "text": "Distortion types:",
                "sub": [
                    'Catastrophizing: "Everything will be terrible".',
                    'Mind-reading: "They think I\'m stupid".',
                    'Personalization: "It\'s definitely because of me".',
                    'Black-and-white thinking: "Either perfect or a failure".',
                ],
            },
            'Ask yourself: "What evidence is FOR and AGAINST this thought?"',
            "Write down an alternative, more realistic thought.",
            "Rate: how did anxiety change (1-10)?",
        ],
        "duration": "10-15 мин",
        "duration_en": "10-15 min",
        "difficulty": "medium",
        "science": None,
        "interactive_url": None,
    },
    {
        "id": 5,
        "slug": "worst-case",
        "category": "cognition",
        "icon": "🧠",
        "title": 'Техника "Наихудший сценарий"',
        "title_en": '"Worst Case Scenario" Technique',
        "summary": "Доведите тревогу до предела, чтобы увидеть её иррациональность",
        "summary_en": "Push the worry to its extreme to expose its irrationality",
        "description": (
            "Доведение тревожной мысли до крайности, чтобы увидеть её "
            "иррациональность и разработать план действий."
        ),
        "description_en": (
            "Take the anxious thought to its extreme to see its "
            "irrationality and build an action plan."
        ),
        "when_to_use": (
            "Когда тревога нарастает перед конкретным событием: "
            "выступлением, встречей, собеседованием."
        ),
        "when_to_use_en": (
            "When anxiety rises before a specific event: a talk, a "
            "meeting, an interview."
        ),
        "steps": [
            'Запишите: "Что самое худшее, что может случиться?"',
            'Запишите: "Что самое лучшее, что может случиться?"',
            'Запишите: "Что скорее всего произойдёт?"',
            'Для наихудшего сценария: "Смогу ли я с этим справиться? Как?"',
            "Оцените: насколько вероятен наихудший сценарий (0-100%)?",
            "Обычно реальная вероятность — менее 5%.",
        ],
        "steps_en": [
            'Write down: "What is the worst that could happen?"',
            'Write down: "What is the best that could happen?"',
            'Write down: "What is most likely to happen?"',
            'For the worst case: "Can I cope with this? How?"',
            "Rate: how likely is the worst case (0-100%)?",
            "Usually the real probability is below 5%.",
        ],
        "duration": "10 мин",
        "duration_en": "10 min",
        "difficulty": "medium",
        "science": None,
        "interactive_url": None,
    },
    {
        "id": 6,
        "slug": "stop-method",
        "category": "cognition",
        "icon": "🧠",
        "title": "Метод СТОП",
        "title_en": "STOP Method",
        "summary": "Прервите спираль тревоги в 4 шага: Стоп, Тело, Обзор, План",
        "summary_en": "Break the anxiety spiral in 4 steps: Stop, Body, Overview, Plan",
        "description": (
            "Быстрая техника прерывания спирали тревожных мыслей в 4 шага."
        ),
        "description_en": (
            "A fast 4-step technique to interrupt a spiral of anxious thoughts."
        ),
        "when_to_use": (
            "В момент, когда замечаете нарастание тревожных мыслей."
        ),
        "when_to_use_en": (
            "The moment you notice anxious thoughts growing."
        ),
        "steps": [
            'С — Стоп! Мысленно скажите себе "СТОП" и представьте красный знак.',
            "Т — Тело: обратите внимание на своё тело, где напряжение?",
            "О — Обзор: осмотритесь вокруг, что вы видите, слышите, чувствуете?",
            "П — План: что я сделаю прямо сейчас? (одно конкретное действие)",
        ],
        "steps_en": [
            'S — Stop! Mentally tell yourself "STOP" and picture a red sign.',
            "T — Take stock of your body: where is tension held?",
            "O — Observe around you: what do you see, hear, feel?",
            "P — Plan: what will I do right now? (one concrete action)",
        ],
        "duration": "1-2 мин",
        "duration_en": "1-2 min",
        "difficulty": "easy",
        "science": None,
        "interactive_url": None,
    },

    # ============== BODY ==============
    {
        "id": 7,
        "slug": "pmr",
        "category": "body",
        "icon": "🧘",
        "title": "Прогрессивная мышечная релаксация (PMR)",
        "title_en": "Progressive Muscle Relaxation (PMR)",
        "summary": "Последовательное напряжение и расслабление мышц",
        "summary_en": "Sequential tensing and relaxing of muscle groups",
        "description": (
            "Последовательное напряжение и расслабление групп мышц — "
            "снимает физическое напряжение, которое сопровождает тревогу."
        ),
        "description_en": (
            "Sequential tensing and relaxing of muscle groups — releases "
            "physical tension that accompanies anxiety."
        ),
        "when_to_use": (
            "При мышечном напряжении, скованности, головной боли от стресса, "
            "перед сном."
        ),
        "when_to_use_en": (
            "With muscle tension, stiffness, stress headache, before sleep."
        ),
        "steps": [
            "Лягте или сядьте удобно, закройте глаза.",
            "Начните с ног: напрягите мышцы стоп на 5 секунд, затем расслабьте на 10 секунд.",
            "Голени: напрягите на 5 сек → расслабьте на 10 сек.",
            "Бёдра: напрягите → расслабьте.",
            "Живот: напрягите → расслабьте.",
            "Руки и кисти: сожмите кулаки → расслабьте.",
            "Плечи: поднимите к ушам → расслабьте.",
            "Лицо: сожмите все мышцы → расслабьте.",
            "Почувствуйте разницу между напряжением и расслаблением.",
            "Сделайте 3 глубоких вдоха.",
        ],
        "steps_en": [
            "Lie down or sit comfortably, close your eyes.",
            "Start with the feet: tense for 5 seconds, then relax for 10 seconds.",
            "Calves: tense 5s → relax 10s.",
            "Thighs: tense → relax.",
            "Abdomen: tense → relax.",
            "Hands and fists: clench → relax.",
            "Shoulders: raise to ears → relax.",
            "Face: tense all muscles → relax.",
            "Feel the difference between tension and relaxation.",
            "Take 3 deep breaths.",
        ],
        "duration": "15-20 мин",
        "duration_en": "15-20 min",
        "difficulty": "easy",
        "science": None,
        "interactive_url": None,
    },
    {
        "id": 8,
        "slug": "grounding-54321",
        "category": "body",
        "icon": "🧘",
        "title": "Заземление 5-4-3-2-1",
        "title_en": "5-4-3-2-1 Grounding",
        "summary": "Возвращение в настоящий момент через 5 органов чувств",
        "summary_en": "Come back to the present through the five senses",
        "description": (
            "Быстрая техника возвращения в настоящий момент через "
            "5 органов чувств."
        ),
        "description_en": (
            "A fast technique to return to the present moment through "
            "the five senses."
        ),
        "when_to_use": (
            "При панической атаке, диссоциации, ощущении нереальности."
        ),
        "when_to_use_en": (
            "During a panic attack, dissociation, sense of unreality."
        ),
        "steps": [
            "Назовите 5 вещей, которые вы ВИДИТЕ.",
            "Назовите 4 звука, которые вы СЛЫШИТЕ.",
            "Назовите 3 вещи, которые вы можете ПОТРОГАТЬ.",
            "Назовите 2 запаха, которые вы ЧУВСТВУЕТЕ.",
            "Назовите 1 вкус, который вы ОЩУЩАЕТЕ.",
            "Сделайте 3 глубоких вдоха.",
        ],
        "steps_en": [
            "Name 5 things you can SEE.",
            "Name 4 sounds you can HEAR.",
            "Name 3 things you can TOUCH.",
            "Name 2 smells you can FEEL.",
            "Name 1 taste you can SENSE.",
            "Take 3 deep breaths.",
        ],
        "duration": "3-5 мин",
        "duration_en": "3-5 min",
        "difficulty": "easy",
        "science": None,
        "interactive_url": "/sos/grounding",
        "interactive_label": "Интерактивная версия",
        "interactive_label_en": "Interactive version",
    },
    {
        "id": 9,
        "slug": "positive-visualization",
        "category": "body",
        "icon": "🧘",
        "title": "Позитивная визуализация",
        "title_en": "Positive Visualization",
        "summary": "Мысленное проживание успешного сценария тревожной ситуации",
        "summary_en": "Mentally rehearse a successful version of an anxious situation",
        "description": (
            "Мысленное проживание успешного сценария — тренирует мозг "
            "реагировать спокойнее в реальной ситуации."
        ),
        "description_en": (
            "Mentally living through a successful scenario — trains the "
            "brain to react calmer in the real situation."
        ),
        "when_to_use": (
            "За день или несколько часов до тревожного события."
        ),
        "when_to_use_en": (
            "A day or several hours before an anxiety-inducing event."
        ),
        "steps": [
            "Закройте глаза, сделайте 3 глубоких вдоха.",
            "Представьте тревожную ситуацию (например, выступление).",
            "Но представьте, что ВСЁ ИДЁТ ХОРОШО: вы говорите уверенно, люди слушают.",
            "Добавьте детали: что вы видите, слышите, чувствуете.",
            "Представьте, как вы заканчиваете и чувствуете облегчение и гордость.",
            'Откройте глаза и запишите: "Я могу с этим справиться".',
            "Повторяйте перед каждым тревожным событием.",
        ],
        "steps_en": [
            "Close your eyes, take 3 deep breaths.",
            "Picture the anxiety-inducing situation (e.g., a presentation).",
            "But picture EVERYTHING GOING WELL: you speak confidently, people listen.",
            "Add details: what you see, hear, feel.",
            "Picture finishing and feeling relief and pride.",
            'Open your eyes and write: "I can handle this."',
            "Repeat before every anxiety-inducing event.",
        ],
        "duration": "5-10 мин",
        "duration_en": "5-10 min",
        "difficulty": "medium",
        "science": None,
        "interactive_url": None,
    },
]


# ===================== локализация =====================

EN_FIELDS = [
    ("title_en", "title"),
    ("summary_en", "summary"),
    ("description_en", "description"),
    ("when_to_use_en", "when_to_use"),
    ("steps_en", "steps"),
    ("science_en", "science"),
    ("duration_en", "duration"),
    ("interactive_label_en", "interactive_label"),
]


def _current_locale() -> str:
    try:
        from flask import g, has_request_context
        if has_request_context():
            loc = getattr(g, "locale", None)
            if loc in ("en", "ru"):
                return loc
    except Exception:
        pass
    return "en"


def _apply_locale(tip: dict) -> dict:
    out = dict(tip)
    if _current_locale() == "en":
        for src, dst in EN_FIELDS:
            v = tip.get(src)
            if v is not None:
                out[dst] = v
    return out


def get_tip(identifier):
    if identifier is None:
        return None
    for t in TIPS:
        if str(t["id"]) == str(identifier) or t["slug"] == str(identifier):
            return _apply_locale(t)
    return None


def get_tips_by_category(category=None):
    if not category or category == "all":
        return [_apply_locale(t) for t in TIPS]
    return [_apply_locale(t) for t in TIPS if t["category"] == category]


def localized_categories() -> dict:
    return CATEGORIES_BY_LOCALE.get(_current_locale(),
                                    CATEGORIES_BY_LOCALE["en"])


def localized_difficulty_labels() -> dict:
    return DIFFICULTY_LABELS_BY_LOCALE.get(_current_locale(),
                                           DIFFICULTY_LABELS_BY_LOCALE["en"])
