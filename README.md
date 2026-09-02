# Samsung Phone Query and Review System

Scrapes specs for 15 Samsung phones from GSMArena into PostgreSQL (Neon),
answers natural-language questions about them via a RAG chatbot (pgvector +
Groq), and generates structured product reviews via a two-agent LangChain
pipeline — all exposed through a FastAPI service.

## Architecture

```
GSMArena  --scrape-->  PostgreSQL/Neon  --embed-->  pgvector table
                            |                            |
                            v                            v
                  LangChain agents  <-------  RAG chain (ChatGroq)
                  (Data Specialist                    |
                   + Review Generator)                 |
                            |                           |
                            v                           v
                       FastAPI: POST /review     FastAPI: POST /ask
```

- **Scraper** (`app/scraper/`): `requests` + `BeautifulSoup` against a curated,
  pre-verified list of 15 GSMArena spec pages (GSMArena's search endpoint is
  behind a Cloudflare challenge, so it can't be crawled dynamically). Parses
  both a machine-readable `data-spec`-keyed dict and a full labeled walk of
  every section, so nothing scraped is lost.
- **Database** (`app/db/`): two tables — `phones` and `specifications` (1:1) —
  plus a `phone_embeddings` table managed by `langchain-postgres`. Structured
  columns (display, camera, battery, processor, memory, price...) drive fast
  SQL lookups; a `raw_specs_json`/`raw_text` pair preserves the full scrape for
  the RAG document builder.
- **RAG chatbot** (`app/rag/`): local `sentence-transformers`
  (`all-MiniLM-L6-v2`) embeddings stored in Postgres via `pgvector`, queried by
  `ChatGroq` via a hand-rolled LangChain LCEL chain. Two extra routing steps
  fix the weak spots of plain top-k similarity search over a 15-document
  corpus: a superlative router (`sql_router.py`) answers "best/worst X"
  questions with a real SQL `ORDER BY` instead of guessing, and an alias
  matcher (`phone_matcher.py`) force-includes every phone a question names so
  comparison questions ("S23 vs S22") always see both phones.
- **Multi-agent system** (`app/agents/`): plain LangChain, also on Groq. A
  **Data Specialist** agent (`langchain_classic` tool-calling `AgentExecutor`)
  retrieves a phone's specs from Postgres via a tool; a second **Review
  Generator** agent turns those specs into a Markdown review (Summary / Pros /
  Cons / Rating).

## Implementation Notes

### 1. Four connected components

The system is organized into four connected parts: a GSMArena scraper, a
structured PostgreSQL database, a RAG chatbot with a multi-agent review flow,
and a FastAPI service. Keeping these concerns in separate modules makes each
part independently testable while allowing them to work as one pipeline.

### 2. Selected and verified the phone catalog

The project uses a curated catalog of 15 Samsung models covering the Galaxy S21,
S22, S23 and S24 families, plus popular A-series and foldable devices. Each
entry maps a canonical phone name to its GSMArena specification-page URL in
`app/scraper/phone_urls.py`. The companion script
`scripts/verify_gsmarena_urls.py` fetches every URL and compares its page title
with the expected model, preventing a changed or incorrect URL from silently
polluting the database.

### 3. Built the GSMArena scraper

`app/scraper/gsmarena_scraper.py` first requests each page with a browser user
agent, retry and polite delay. BeautifulSoup then reads GSMArena's
`#specs-list` tables in two ways:

- a flat dictionary keyed by stable `data-spec` attributes for structured
  values;
- a section/label dictionary that preserves the complete specification sheet.

The parser extracts display, chipset, CPU, GPU, memory, cameras, battery,
charging, weight, release year and USD price. It also retains GSMArena's
multi-currency price text and both generations of battery test results:
active-use hours and the legacy endurance rating. If normal HTTP requests are
blocked, `selenium_fallback.py` retries the page through headless Chrome.

### 4. Stored both structured and full-fidelity data

The SQLAlchemy models in `app/db/models.py` define a `phones` table and a
one-to-one `specifications` table. Frequently queried facts live in typed
columns so the application can sort and filter them accurately. The complete
scrape is also stored as JSON and plain text, ensuring less-common GSMArena
fields remain available to retrieval and review generation.

`python -m app.scraper.run_scrape` creates the schema and upserts all 15
phones. Re-running it updates existing rows instead of creating duplicates.
`python -m scripts.backfill_structured_fields` safely upgrades an older
database and derives the newer battery and price fields from its stored raw
data.

### 5. Created the vector index

`app/ingest.py` converts every database record into a LangChain document. A
local `all-MiniLM-L6-v2` sentence-transformer creates 384-dimensional
embeddings, and `langchain-postgres` stores them in the `phone_embeddings`
pgvector table. Deterministic UUIDs make indexing idempotent, so an updated
phone replaces its previous embedding rather than adding a duplicate.

### 6. Built retrieval that handles real user questions

The chatbot combines three retrieval strategies before calling the language
model:

1. `phone_matcher.py` recognizes aliases such as `S23`, `Galaxy S23`,
   `S23+`, and `S23 Ultra` without confusing base and Plus models.
2. `sql_router.py` detects measurable superlatives such as best battery life,
   largest battery, fastest charging or cheapest price and answers them using
   a real SQL minimum/maximum query.
3. pgvector similarity search retrieves other semantically relevant phones.

The selected records are converted to compact context and passed to a strict
RAG prompt that permits answers only from the supplied database facts. This
supports specification, recommendation and comparison questions while
reducing unsupported claims.

### 7. Implemented the two-agent review workflow

The review pipeline in `app/agents/review_pipeline.py` has two specialized
LangChain agents:

- **Data Specialist Agent** calls a database tool to retrieve the requested
  phone's complete technical specification sheet.
- **Review Generator Agent** receives those verified specifications and writes
  a balanced Markdown review containing Summary, Pros, Cons and a 1-5 star
  Rating.

Separating retrieval from writing ensures the reviewer works from database
evidence rather than trying to remember product details.

### 8. Exposed the system through FastAPI

`app/api/main.py` initializes the database schema, vector store, chatbot and
review agents once during application startup. The API provides:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Basic service health check |
| `GET` | `/phones` | List all stored phones and structured specs |
| `GET` | `/phones/{name}` | Retrieve one phone using a full name or alias |
| `POST` | `/ask` | Ask specification, ranking or comparison questions |
| `POST` | `/review` | Generate a two-agent product review |

Pydantic validates and trims request input. Unknown or ambiguous phone names
return `404`, invalid payloads return `422`, and temporarily unavailable model
services return `503` instead of an unexplained server error.

### 9. Fixed the main retrieval edge cases

The final matching logic keeps `S23` separate from `S23+`, resolves aliases
before attempting partial matches, and refuses to guess when a partial name
matches multiple phones. Battery-life questions use GSMArena's measured
active-use score when available, while battery-capacity questions remain a
separate SQL metric. Prices without a real USD value are not mislabeled as
dollars; the original multi-currency text is preserved instead.

### 10. Automated and live verification

The `tests/` suite covers alias collisions, comparison extraction, GSMArena
parsing, battery routing, price handling and API input validation. The
end-to-end verification process is:

```text
GSMArena URL check -> scrape/upsert -> structured-field backfill
                    -> pgvector indexing -> pytest
                    -> Swagger/API query and review demonstration
```

All 15 curated GSMArena URLs, database rows and vector records can be
verified through this pipeline before deployment.

## Setup

### 1. Python environment

```
python -m venv venv
venv\Scripts\activate        # PowerShell: venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. PostgreSQL (Neon)

Create a free project on [Neon](https://neon.tech), copy its connection
string, and use the `postgresql+psycopg://...` form (psycopg v3 — required by
`langchain-postgres`) in `DATABASE_URL`. The pgvector extension ships with
every Neon database; the app enables it automatically
(`CREATE EXTENSION IF NOT EXISTS vector`) the first time it connects.

### 3. API key

- `GROQ_API_KEY` — free, from [console.groq.com](https://console.groq.com).

Copy `.env.example` to `.env` and fill in `DATABASE_URL` and `GROQ_API_KEY`.
`GROQ_MODEL` defaults to `openai/gpt-oss-120b` (Groq's free/developer-tier
recommendation — `llama-3.3-70b-versatile` is Enterprise-only as of mid-2026);
change it if you have paid Groq access.

### 4. Scrape and index

```
python -m app.scraper.run_scrape   # populates PostgreSQL (~15 phones)
python -m scripts.backfill_structured_fields  # safe/idempotent schema + derived-field update
python -m app.ingest                # embeds them into the pgvector table
```

## Example requests

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"What are the camera specs of the Samsung Galaxy S23?\"}"

curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"Which Samsung phone has the best battery life?\"}"

curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"How does the Galaxy S23 compare to the S22 in terms of performance?\"}"

curl -X POST http://127.0.0.1:8000/review \
  -H "Content-Type: application/json" \
  -d "{\"phone_name\": \"Samsung Galaxy S23\"}"

curl http://127.0.0.1:8000/phones
```

## Project layout

```
app/
├── config.py          # env-driven settings
├── db/                  # SQLAlchemy models, session, CRUD
├── scraper/              # GSMArena fetch + parse + CLI
├── rag/                   # documents, alias matcher, SQL router, pgvector store, RAG chain
├── agents/                # LangChain tool, Data Specialist agent, Review Generator chain
├── api/                   # FastAPI app, schemas, routers
└── ingest.py              # embeds the DB's phones into the pgvector table
scripts/
└── verify_gsmarena_urls.py  # preflight check on the curated phone URL list
```
