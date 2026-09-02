from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.config import settings
from app.db.crud import get_all_phones, get_best_by_spec
from app.rag.documents import build_phone_summary
from app.rag.phone_matcher import build_alias_map, extract_mentioned_phones
from app.rag.sql_router import detect_superlative

PROMPT = ChatPromptTemplate.from_template(
    "You are a knowledgeable Samsung phone expert assistant. Answer the user's "
    "question using ONLY the context below. If the question compares two or "
    "more phones, address each one explicitly. If the context doesn't contain "
    "the answer, say so honestly instead of guessing.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}\n\n"
    "Answer:"
)

# Cap on how many phones' worth of context get bundled into one call - keeps
# requests comfortably under Groq's free-tier tokens-per-minute limit even
# though the full pgvector index (used for search) holds the longer,
# full-detail documents.
MAX_CONTEXT_PHONES = 4


class RagChatbot:
    """Ties SQL superlative routing + alias-forced retrieval + pgvector
    similarity search into one context, then answers via ChatGroq. Built once
    at API startup and reused across requests."""

    def __init__(self, session_factory, vectorstore):
        self.session_factory = session_factory
        self.vectorstore = vectorstore
        self.llm = ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key, temperature=0.2)
        self.chain = PROMPT | self.llm | StrOutputParser()

        with session_factory() as session:
            phones = get_all_phones(session)
            self.summary_by_name = {p.name: build_phone_summary(p) for p in phones if p.specification is not None}
        self.alias_map = build_alias_map(list(self.summary_by_name.keys()))

    def _sql_hit_names(self, question: str) -> list[str]:
        hit = detect_superlative(question)
        if not hit:
            return []
        column_key, direction = hit
        with self.session_factory() as session:
            phones = get_best_by_spec(session, column_key, direction, limit=MAX_CONTEXT_PHONES)
            return [phone.name for phone in phones]

    def _build_context(self, question: str) -> str:
        names: list[str] = []

        def add(name: str | None) -> None:
            if name and name in self.summary_by_name and name not in names:
                names.append(name)

        for name in self._sql_hit_names(question):
            add(name)

        for name in extract_mentioned_phones(question, self.alias_map):
            add(name)

        for doc in self.vectorstore.similarity_search(question, k=4):
            add(doc.metadata.get("phone_name"))

        summaries = [self.summary_by_name[name] for name in names[:MAX_CONTEXT_PHONES]]
        return "\n\n---\n\n".join(summaries)

    def answer(self, question: str) -> str:
        context = self._build_context(question)
        return self.chain.invoke({"context": context, "question": question})
