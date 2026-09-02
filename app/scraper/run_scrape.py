"""CLI entrypoint: scrape every phone in PHONE_URLS and upsert into Postgres.

Usage:
    python -m app.scraper.run_scrape
"""

from __future__ import annotations

from app.db.crud import upsert_phone
from app.db.session import SessionLocal, init_db
from app.scraper.gsmarena_scraper import (
    ScraperError,
    fetch_page,
    flatten_to_text,
    map_to_structured_columns,
    parse_full_sections,
    parse_spec_page,
    slugify,
)
from app.scraper.phone_urls import PHONE_URLS
from app.scraper.selenium_fallback import fetch_with_selenium


def scrape_one(session, name: str, url: str) -> None:
    try:
        html = fetch_page(url)
    except ScraperError:
        print(f"  requests failed for {name}, falling back to Selenium...")
        html = fetch_with_selenium(url)

    flat = parse_spec_page(html)
    sections = parse_full_sections(html)
    structured, release_year = map_to_structured_columns(flat, sections)
    raw_text = flatten_to_text(sections)

    upsert_phone(
        session,
        name=name,
        slug=slugify(name),
        gsmarena_url=url,
        release_year=release_year,
        structured=structured,
        raw_specs_json=sections,
        raw_text=raw_text,
    )


def main() -> None:
    init_db()
    session = SessionLocal()
    succeeded, failed = [], []
    try:
        for name, url in PHONE_URLS.items():
            print(f"Scraping {name} ...")
            try:
                scrape_one(session, name, url)
                succeeded.append(name)
            except Exception as exc:  # noqa: BLE001 - report and continue with the rest
                print(f"  FAILED: {name}: {exc}")
                failed.append(name)
    finally:
        session.close()

    print(f"\nDone. {len(succeeded)} succeeded, {len(failed)} failed.")
    if failed:
        print("Failed:", ", ".join(failed))


if __name__ == "__main__":
    main()
