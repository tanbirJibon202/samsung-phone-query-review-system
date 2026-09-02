from langchain_core.tools import tool

from app.db.crud import get_phone_by_name
from app.db.session import SessionLocal
from app.rag.documents import build_phone_document


@tool
def get_phone_specs_tool(phone_name: str) -> str:
    """Look up the full technical specifications for a Samsung phone by model
    name (e.g. 'Samsung Galaxy S23' or just 'S23'). Returns display, camera,
    battery, processor, memory and other specs as text."""
    session = SessionLocal()
    try:
        phone = get_phone_by_name(session, phone_name)
        if phone is None or phone.specification is None:
            return f"No specifications found for '{phone_name}'."
        return build_phone_document(phone)
    finally:
        session.close()
