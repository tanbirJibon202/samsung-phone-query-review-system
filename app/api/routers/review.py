import logging

from fastapi import APIRouter, HTTPException, Request

from app.api.schemas import ReviewRequest, ReviewResponse
from app.db.crud import get_phone_by_name
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)
router = APIRouter(tags=["multi-agent"])


@router.post("/review", response_model=ReviewResponse)
def review(payload: ReviewRequest, request: Request) -> ReviewResponse:
    session = SessionLocal()
    try:
        phone = get_phone_by_name(session, payload.phone_name)
    finally:
        session.close()

    if phone is None:
        raise HTTPException(status_code=404, detail=f"Unknown phone '{payload.phone_name}'")

    try:
        review_text = request.app.state.review_pipeline.run(phone.name)
    except Exception as exc:
        logger.exception("Review generation failed for %r", phone.name)
        raise HTTPException(status_code=503, detail="Review service is temporarily unavailable") from exc
    return ReviewResponse(phone_name=phone.name, review=review_text)
