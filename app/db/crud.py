from sqlalchemy import ColumnElement, func
from sqlalchemy.orm import Session

from app.db.models import Phone, Specification

# Whitelist of columns that may be used for "best/worst X" superlative queries.
# Keeping this as a fixed mapping (rather than resolving arbitrary column names
# from user text) avoids ever building SQL from unsanitized input.
SPEC_COLUMNS: dict[str, ColumnElement] = {
    "battery_active_use_hours": Specification.battery_active_use_hours,
    "battery_endurance_hours": Specification.battery_endurance_hours,
    "battery_capacity_mah": Specification.battery_capacity_mah,
    "rear_camera_mp": Specification.rear_camera_mp,
    "front_camera_mp": Specification.front_camera_mp,
    "ram_gb": Specification.ram_gb,
    "storage_gb": Specification.storage_gb,
    "display_size_in": Specification.display_size_in,
    "charging_speed_w": Specification.charging_speed_w,
    "price_usd": Specification.price_usd,
}


def upsert_phone(
    session: Session,
    *,
    name: str,
    slug: str,
    gsmarena_url: str,
    release_year: int | None,
    structured: dict,
    raw_specs_json: dict,
    raw_text: str,
) -> Phone:
    phone = session.query(Phone).filter(Phone.slug == slug).one_or_none()
    if phone is None:
        phone = Phone(name=name, slug=slug, gsmarena_url=gsmarena_url, release_year=release_year)
        session.add(phone)
        session.flush()  # assigns phone.id
        phone.specification = Specification(phone_id=phone.id, raw_specs_json=raw_specs_json, raw_text=raw_text)
    else:
        phone.name = name
        phone.gsmarena_url = gsmarena_url
        phone.release_year = release_year
        if phone.specification is None:
            phone.specification = Specification(phone_id=phone.id, raw_specs_json=raw_specs_json, raw_text=raw_text)
        else:
            phone.specification.raw_specs_json = raw_specs_json
            phone.specification.raw_text = raw_text

    for key, value in structured.items():
        setattr(phone.specification, key, value)

    session.commit()
    session.refresh(phone)
    return phone


def get_all_phones(session: Session) -> list[Phone]:
    return session.query(Phone).order_by(Phone.name).all()


def get_phone_by_name(session: Session, name: str) -> Phone | None:
    """Case-insensitive exact match, then alias resolution, then a unique partial match
    (e.g. "S23" -> "Samsung Galaxy S23")."""
    name = name.strip()

    phone = session.query(Phone).filter(Phone.name.ilike(name)).one_or_none()
    if phone:
        return phone

    from app.rag.phone_matcher import build_alias_map, resolve_alias

    all_names = [p.name for p in get_all_phones(session)]
    resolved = resolve_alias(name, build_alias_map(all_names))
    if resolved:
        return session.query(Phone).filter(Phone.name == resolved).one_or_none()

    # Partial names such as "Ultra" may match several phones. Return no match
    # instead of raising MultipleResultsFound or silently choosing the wrong one.
    matches = session.query(Phone).filter(Phone.name.ilike(f"%{name}%")).limit(2).all()
    if len(matches) == 1:
        return matches[0]

    return None


def get_best_by_spec(session: Session, column_key: str, direction: str, limit: int = 1) -> list[Phone]:
    column = SPEC_COLUMNS.get(column_key)
    if column is None:
        return []
    aggregate = func.max(column) if direction == "desc" else func.min(column)
    extreme_value = session.query(aggregate).filter(column.is_not(None)).scalar()
    if extreme_value is None:
        return []
    return (
        session.query(Phone)
        .join(Specification)
        .filter(column == extreme_value)
        .order_by(Phone.name)
        .limit(limit)
        .all()
    )
