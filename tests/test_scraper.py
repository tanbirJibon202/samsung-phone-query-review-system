import pytest

from app.scraper.gsmarena_scraper import (
    ScraperError,
    extract_battery_and_price_fields,
    map_to_structured_columns,
    parse_spec_page,
    slugify,
)


def test_extracts_real_battery_life_and_price_summary() -> None:
    sections = {
        "Battery": {"Charging": "25W wired, 15W wireless"},
        "Our Tests": {"Battery": "Active use score 11:27h", "Battery (old)": "Endurance rating 101h"},
        "Misc": {"Price": "$ 261.31 / EUR 259.24"},
    }

    fields = extract_battery_and_price_fields(sections)

    assert fields["battery_active_use_hours"] == pytest.approx(11.45)
    assert fields["battery_endurance_hours"] == 101
    assert fields["price_summary"] == "$ 261.31 / EUR 259.24"


def test_structured_mapping_keeps_usd_distinct_from_other_currencies() -> None:
    flat = {
        "year": "2023, February 01",
        "internalmemory": "128GB 8GB RAM, 256GB 8GB RAM",
        "batdescription1": "Li-Ion 3900 mAh",
        "price": "EUR 259.24",
    }
    structured, year = map_to_structured_columns(flat, {"Misc": {"Price": "EUR 259.24"}})

    assert year == 2023
    assert structured["storage_gb"] == 128
    assert structured["ram_gb"] == 8
    assert structured["battery_capacity_mah"] == 3900
    assert structured["price_usd"] is None
    assert structured["price_summary"] == "EUR 259.24"


def test_parser_reports_changed_markup() -> None:
    with pytest.raises(ScraperError):
        parse_spec_page("<html><body>No specs here</body></html>")


def test_slugify_preserves_plus_meaning() -> None:
    assert slugify("Samsung Galaxy S23+") == "samsung_galaxy_s23_plus"
