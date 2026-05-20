from flask_babel import lazy_gettext as _


EMOTIONS = [
    ("fear", _("Fear")),
    ("shame", _("Shame")),
    ("loneliness", _("Loneliness")),
    ("irritation", _("Irritation")),
    ("sadness", _("Sadness")),
    ("guilt", _("Guilt")),
    ("helplessness", _("Helplessness")),
    ("tension", _("Tension")),
    ("insecurity", _("Insecurity")),
    ("embarrassment", _("Embarrassment")),
    ("panic", _("Panic")),
    ("depression", _("Depression")),
]


EMOTION_KEYS = {key for key, _label in EMOTIONS}


def normalize_emotions(values: list[str]) -> list[str]:
    return [value for value in values if value in EMOTION_KEYS]


def emotion_label(key: str) -> str:
    return dict(EMOTIONS).get(key, key)
