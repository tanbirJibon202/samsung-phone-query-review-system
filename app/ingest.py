"""CLI entrypoint: (re)build the pgvector embeddings table from whatever is
currently in Postgres.

Run this after app.scraper.run_scrape has populated the database, and again
any time the data changes.

Usage:
    python -m app.ingest
"""

import uuid

from app.db.session import SessionLocal
from app.rag.documents import load_all_documents_from_db
from app.rag.vectorstore import get_vectorstore

# PGVectorStore's id column is UUID-typed, so plain integer phone ids can't be
# used directly. Deriving a UUID from the phone id keeps it deterministic -
# re-running this script upserts instead of piling up duplicate rows.
ID_NAMESPACE = uuid.UUID("d6f0a7b0-6e2e-4e6a-9c1e-4a1a7f8b6c2d")


def main() -> None:
    session = SessionLocal()
    try:
        documents = load_all_documents_from_db(session)
    finally:
        session.close()

    if not documents:
        print("No phones found in the database - run `python -m app.scraper.run_scrape` first.")
        return

    store = get_vectorstore()
    ids = [str(uuid.uuid5(ID_NAMESPACE, str(doc.metadata["phone_id"]))) for doc in documents]
    store.add_documents(documents, ids=ids)
    print(f"Indexed {len(documents)} phones into the pgvector store.")


if __name__ == "__main__":
    main()
