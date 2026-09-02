from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import PhoneOut
from app.db.crud import get_all_phones, get_phone_by_name
from app.db.session import get_db

router = APIRouter(tags=["phones"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/phones", response_model=list[PhoneOut])
def list_phones(db: Session = Depends(get_db)) -> list[PhoneOut]:
    return [PhoneOut.from_phone(phone) for phone in get_all_phones(db)]


@router.get("/phones/{name}", response_model=PhoneOut)
def get_phone(name: str, db: Session = Depends(get_db)) -> PhoneOut:
    phone = get_phone_by_name(db, name)
    if phone is None:
        raise HTTPException(status_code=404, detail=f"Unknown phone '{name}'")
    return PhoneOut.from_phone(phone)
