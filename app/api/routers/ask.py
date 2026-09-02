import logging

from fastapi import APIRouter, HTTPException, Request

from app.api.schemas import AskRequest, AskResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chatbot"])


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, request: Request) -> AskResponse:
    try:
        answer = request.app.state.rag.answer(payload.question)
    except Exception as exc:
        logger.exception("RAG answer failed for question %r", payload.question)
        raise HTTPException(status_code=503, detail="Chatbot service is temporarily unavailable") from exc
    return AskResponse(question=payload.question, answer=answer)
