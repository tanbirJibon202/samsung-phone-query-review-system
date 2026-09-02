from langchain_core.documents import Document
from sqlalchemy.orm import Session

from app.db.crud import get_all_phones
from app.db.models import Phone


def _summary_lines(phone: Phone) -> list[str]:
    s = phone.specification
    lines = [
        f"Phone: {phone.name}",
        f"Display: {s.display_size_in}\" {s.display_type or ''}, {s.display_resolution or ''}".strip(),
        f"Processor: {s.chipset or 'N/A'} (CPU: {s.cpu or 'N/A'}, GPU: {s.gpu or 'N/A'})",
        f"Memory: {s.ram_gb or '?'}GB RAM, {s.storage_gb or '?'}GB storage",
        f"Main Camera: {s.rear_camera_summary or 'N/A'}",
        f"Front Camera: {s.front_camera_mp or '?'} MP",
        (
            f"Battery: {s.battery_capacity_mah or '?'} mAh, charging up to {s.charging_speed_w or '?'}W, "
            f"active-use test {s.battery_active_use_hours:.2f}h"
            if s.battery_active_use_hours is not None
            else f"Battery: {s.battery_capacity_mah or '?'} mAh, charging up to {s.charging_speed_w or '?'}W"
        ),
        f"OS: {s.os or 'N/A'}",
        f"Weight: {s.body_weight_g or '?'} g",
    ]
    if s.price_summary:
        lines.append(f"Price: {s.price_summary}")
    elif s.price_usd:
        lines.append(f"Price: approx. ${s.price_usd}")
    return lines


def build_phone_summary(phone: Phone) -> str:
    """Compact spec summary - used for RAG context, where several phones'
    worth of text may be bundled into one LLM call and Groq's free-tier
    tokens-per-minute limit is easy to blow through with full documents."""
    return "\n".join(_summary_lines(phone))


def build_phone_document(phone: Phone) -> str:
    """Full spec sheet (summary + every scraped section) - used for the
    pgvector index (better recall) and the single-phone CrewAI/LangChain
    tool lookup, where token volume isn't a concern."""
    lines = _summary_lines(phone)
    lines.append("\nFull specifications:\n" + phone.specification.raw_text)
    return "\n".join(lines)


def load_all_documents_from_db(session: Session) -> list[Document]:
    return [
        Document(page_content=build_phone_document(phone), metadata={"phone_name": phone.name, "phone_id": phone.id})
        for phone in get_all_phones(session)
        if phone.specification is not None
    ]
