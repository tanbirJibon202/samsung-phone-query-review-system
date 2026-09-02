"""Apply schema upgrades and backfill derived fields from stored raw specs.

Usage:
    python -m scripts.backfill_structured_fields
"""

from app.db.models import Phone
from app.db.session import SessionLocal, init_db
from app.scraper.gsmarena_scraper import extract_battery_and_price_fields


def main() -> None:
    init_db()
    updated = 0
    with SessionLocal() as session:
        phones = session.query(Phone).order_by(Phone.name).all()
        for phone in phones:
            spec = phone.specification
            if spec is None:
                continue
            fields = extract_battery_and_price_fields(spec.raw_specs_json or {})
            for key, value in fields.items():
                setattr(spec, key, value)
            updated += 1
        session.commit()

    print(f"Backfilled structured battery/price fields for {updated} phones.")


if __name__ == "__main__":
    main()
