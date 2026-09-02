from app.rag.sql_router import detect_superlative


def test_battery_life_uses_active_use_score() -> None:
    assert detect_superlative("Which phone has the best battery life?") == (
        "battery_active_use_hours",
        "desc",
    )


def test_battery_capacity_remains_a_separate_query() -> None:
    assert detect_superlative("Which phone has the largest battery?") == (
        "battery_capacity_mah",
        "desc",
    )


def test_cheapest_price_sorts_ascending() -> None:
    assert detect_superlative("Which is the cheapest phone?") == ("price_usd", "asc")
