from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.agents.review_pipeline import build_review_pipeline
from app.api.routers import ask, phones, review
from app.db.session import SessionLocal, init_db
from app.rag.chain import RagChatbot
from app.rag.vectorstore import get_vectorstore


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    vectorstore = get_vectorstore()
    app.state.rag = RagChatbot(SessionLocal, vectorstore)
    app.state.review_pipeline = build_review_pipeline()
    yield


app = FastAPI(title="Samsung Phone Query and Review System", lifespan=lifespan)

app.include_router(ask.router)
app.include_router(review.router)
app.include_router(phones.router)
