from app.rag.phone_matcher import build_alias_map, extract_mentioned_phones, resolve_alias


PHONE_NAMES = [
    "Samsung Galaxy S22 5G",
    "Samsung Galaxy S22+ 5G",
    "Samsung Galaxy S22 Ultra 5G",
    "Samsung Galaxy S23",
    "Samsung Galaxy S23+",
    "Samsung Galaxy S23 Ultra",
]


def test_base_alias_is_not_stolen_by_plus_model() -> None:
    aliases = build_alias_map(PHONE_NAMES)

    assert resolve_alias("S22", aliases) == "Samsung Galaxy S22 5G"
    assert resolve_alias("S23", aliases) == "Samsung Galaxy S23"
    assert resolve_alias("Galaxy S23", aliases) == "Samsung Galaxy S23"


def test_plus_aliases_still_resolve() -> None:
    aliases = build_alias_map(PHONE_NAMES)

    assert resolve_alias("S22+", aliases) == "Samsung Galaxy S22+ 5G"
    assert resolve_alias("S23 plus", aliases) == "Samsung Galaxy S23+"


def test_comparison_extracts_the_two_base_models() -> None:
    aliases = build_alias_map(PHONE_NAMES)

    assert extract_mentioned_phones("Compare Galaxy S23 with S22", aliases) == [
        "Samsung Galaxy S23",
        "Samsung Galaxy S22 5G",
    ]
