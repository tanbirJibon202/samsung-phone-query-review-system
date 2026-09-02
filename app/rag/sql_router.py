"""Routes "which phone has the best/worst X" questions to a real SQL
ORDER BY / LIMIT query instead of hoping semantic search happens to surface
the right phone."""

from __future__ import annotations

SUPERLATIVE_WORDS = {"best", "highest", "most", "largest", "biggest", "top", "fastest", "longest"}
INFERIOR_WORDS = {"worst", "lowest", "smallest", "least", "cheapest"}

# user vocabulary -> Specification column key (see app.db.crud.SPEC_COLUMNS)
SPEC_KEYWORDS: dict[str, str] = {
    "battery life": "battery_active_use_hours",
    "active use": "battery_active_use_hours",
    "endurance": "battery_endurance_hours",
    "battery": "battery_capacity_mah",
    "camera": "rear_camera_mp",
    "selfie": "front_camera_mp",
    "front camera": "front_camera_mp",
    "ram": "ram_gb",
    "memory": "ram_gb",
    "storage": "storage_gb",
    "display": "display_size_in",
    "screen": "display_size_in",
    "charging": "charging_speed_w",
    "price": "price_usd",
    "expensive": "price_usd",
    "cheapest": "price_usd",
}


def detect_superlative(question: str) -> tuple[str, str] | None:
    """Return (column_key, "desc"|"asc") if the question is a superlative
    spec question, else None."""
    q = question.lower()

    if any(word in q for word in SUPERLATIVE_WORDS):
        direction = "desc"
    elif any(word in q for word in INFERIOR_WORDS):
        direction = "asc"
    else:
        return None

    for keyword, column_key in SPEC_KEYWORDS.items():
        if keyword in q:
            return column_key, direction

    return None
