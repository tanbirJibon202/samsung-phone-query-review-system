"""FAISS was swapped for pgvector so embeddings live in the same Postgres/Neon
database as everything else, with no separate index file to manage."""

import asyncio
import sys

if sys.platform == "win32":
    # PGEngine drives psycopg's async mode on a background event loop; psycopg
    # can't use Windows' default ProactorEventLoop, so switch to Selector
    # before PGEngine creates that loop.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGEngine, PGVectorStore
from sqlalchemy import text

from app.config import settings
from app.db.session import engine as sa_engine

TABLE_NAME = "phone_embeddings"
VECTOR_SIZE = 384  # sentence-transformers/all-MiniLM-L6-v2 output dimension


def get_embeddings() -> HuggingFaceEmbeddings:
    """Runs locally via the sentence-transformers library - no API token or
    network call needed at inference time, only for the one-time model download."""
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def _ensure_pgvector_extension() -> None:
    with sa_engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))


def _table_exists(table_name: str) -> bool:
    with sa_engine.connect() as conn:
        return conn.execute(text("SELECT to_regclass(:t)"), {"t": table_name}).scalar() is not None


def get_pg_engine() -> PGEngine:
    return PGEngine.from_connection_string(url=settings.database_url)


def get_vectorstore() -> PGVectorStore:
    """Connects to the pgvector-backed embeddings table, creating it first if
    this is the first run."""
    _ensure_pgvector_extension()
    pg_engine = get_pg_engine()
    if not _table_exists(TABLE_NAME):
        pg_engine.init_vectorstore_table(table_name=TABLE_NAME, vector_size=VECTOR_SIZE)
    return PGVectorStore.create_sync(engine=pg_engine, table_name=TABLE_NAME, embedding_service=get_embeddings())
