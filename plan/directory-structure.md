# Directory Structure

```
large-lecture-model/
│
├── plan/                          # project planning docs (this folder)
│   ├── overview.md
│   └── directory-structure.md
│
├── config/
│   ├── courses.yaml               # per-course config: IDs, tokens, protected assignments
│   └── settings.yaml             # global settings: embedding model, retriever mode, etc.
│
├── data/                          # gitignored entirely
│   ├── raw/                       # scraped content, never committed
│   │   ├── canvas/
│   │   │   └── 6.1220/
│   │   │       ├── assignments.json
│   │   │       ├── announcements.json
│   │   │       ├── syllabus.html
│   │   │       └── files/        # downloaded PDFs, slides
│   │   ├── gradescope/
│   │   │   └── 6.1220/
│   │   │       └── assignments.json
│   │   ├── panopto/
│   │   │   └── 6.1220/
│   │   │       └── transcripts/  # .vtt caption files, one per lecture
│   │   └── piazza/
│   │       └── 6.1220/           # IMMEDIATELY anonymized on write; no raw PII stored
│   │           └── posts.json
│   │
│   ├── manual/                    # drop manually exported files here
│   │   └── 6.1220/
│   │       └── slides/           # PDFs dropped in manually
│   │
│   └── processed/                 # chunked + embedded, ready for indexing
│       ├── chunks/
│       │   └── 6.1220/
│       │       └── *.jsonl        # one file per source type
│       └── graphs/
│           └── 6.1220/
│               └── concept_graph.json
│
├── ingest/                        # Phase 1: scrapers, one module per source
│   ├── __init__.py
│   ├── base.py                    # BaseIngestor interface
│   ├── canvas.py                  # Canvas REST API scraper
│   ├── gradescope.py              # Gradescope session scraper (nyuoss/gradescope-api)
│   ├── panopto.py                 # Panopto transcript downloader
│   ├── piazza.py                  # Piazza API scraper (piazza-api library)
│   └── manual.py                  # watches data/manual/, processes dropped files
│
├── process/                       # Phase 2a-d: transform raw → chunks → embeddings
│   ├── __init__.py
│   ├── chunker.py                 # PDF, .vtt, JSON → text chunks with metadata
│   ├── anonymizer.py              # PII removal: spaCy NER + regex, for Piazza/Gradescope
│   ├── embedder.py                # HuggingFace sentence-transformers wrapper
│   └── tagger.py                  # LLM-assisted topic tagging per chunk
│
├── retrieval/                     # Phase 2e: retrieval backends (modular)
│   ├── __init__.py
│   ├── base.py                    # BaseRetriever interface (retrieve(query) -> [Chunk])
│   ├── vector_store.py            # ChromaDB read/write wrapper
│   ├── graph_store.py             # KuzuDB / NetworkX graph read/write wrapper
│   ├── vector_retriever.py        # semantic similarity search via vector DB
│   ├── graph_retriever.py         # GraphRAG: graph traversal + concept expansion
│   └── hybrid_retriever.py        # combines vector + graph, selectable via config
│
├── llm/                           # Phase 2f: LLM integration
│   ├── __init__.py
│   ├── client.py                  # Anthropic SDK wrapper, prompt caching setup
│   ├── guardrails.py              # academic integrity classifier (pre-filter queries)
│   ├── prompts.py                 # system prompts, few-shot examples
│   └── tools.py                   # LLM tool definitions (search, deadlines, etc.)
│
├── chatbot/                       # Phase 2g: CLI interface (dev/testing)
│   ├── __init__.py
│   └── cli.py                     # interactive CLI REPL
│
├── backend/                       # FastAPI app serving both chatbot and dashboard
│   ├── main.py                    # app entrypoint, mounts all routers
│   ├── routes/
│   │   ├── chat.py                # POST /chat — RAG query endpoint (streaming)
│   │   ├── assignments.py         # GET /assignments — deadlines, status, topic links
│   │   └── materials.py          # GET /materials — search slides, transcripts
│   ├── db.py                      # SQLite via SQLAlchemy (assignments, deadlines, status)
│   └── deps.py                    # shared FastAPI dependencies (retriever, llm client)
│
├── frontend/                      # Next.js + Tailwind (chatbot UI + optional dashboard)
│   ├── app/
│   │   ├── page.tsx               # root — redirects to /chat
│   │   ├── chat/
│   │   │   └── page.tsx           # chatbot UI with streaming responses + citations
│   │   └── dashboard/             # Phase 3: assignment tracker, topic map, calendar
│   │       └── page.tsx
│   ├── components/
│   │   ├── ChatWindow.tsx         # message thread, streaming, citation cards
│   │   ├── SourceCard.tsx         # cited chunk: source, lecture title, timestamp/page
│   │   ├── AssignmentList.tsx     # deadline tracker with status badges
│   │   └── TopicMap.tsx          # Phase 3: visual topic → lecture/pset graph
│   ├── lib/
│   │   └── api.ts                 # typed fetch wrappers for backend routes
│   ├── public/
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── scripts/
│   ├── run_ingest.py              # run all scrapers for a given course
│   ├── run_process.py             # chunk + embed + index everything in data/raw/
│   └── run_pipeline.py            # end-to-end: ingest → process → index
│
├── tests/
│   ├── test_chunker.py
│   ├── test_anonymizer.py
│   ├── test_retrieval.py
│   └── test_guardrails.py
│
├── .env.example                   # template for secrets (never commit .env)
├── .gitignore                     # data/, .env, __pycache__, chroma_db/, etc.
├── pyproject.toml                 # dependencies + project metadata (uv or poetry)
├── requirements.txt               # pinned deps for reproducibility
└── README.md
```

---

## Config File Shapes

### `config/courses.yaml`
```yaml
courses:
  6.1220:
    name: "Design and Analysis of Algorithms"
    canvas_course_id: "12345"
    gradescope_course_id: "67890"
    panopto_folder_id: "abcd-..."
    piazza_course_id: "xyz123"
    protected_assignments:          # guardrail: LLM will not solve these
      - "Problem Set 1"
      - "Problem Set 2"
      - "Midterm"
      - "Final"
    protected_window: "until_grades_released"   # or "always" or "until: 2025-05-01"
```

### `config/settings.yaml`
```yaml
embedding:
  model: "BAAI/bge-small-en-v1.5"   # or "nomic-ai/nomic-embed-text-v1"
  device: "cpu"                      # or "cuda"

retrieval:
  mode: "hybrid"                     # "vector" | "graph" | "hybrid"
  top_k: 8

guardrails:
  sensitivity: "permissive"          # "conservative" | "permissive"
  # conservative: block any query mentioning a protected assignment name
  # permissive: block only queries with clear solution-seeking intent

llm:
  model: "claude-sonnet-4-6"
  max_tokens: 2048
```

---

## Key Interfaces

### `BaseIngestor` (ingest/base.py)
```python
class BaseIngestor:
    def __init__(self, course_id: str, config: dict): ...
    def fetch(self) -> list[RawDocument]: ...
    def save(self, docs: list[RawDocument], out_dir: Path): ...
```

### `BaseRetriever` (retrieval/base.py)
```python
class BaseRetriever:
    def retrieve(self, query: str, top_k: int, filters: dict) -> list[Chunk]: ...
```

### `Chunk` data model
```python
@dataclass
class Chunk:
    id: str
    text: str
    source: str          # "canvas" | "panopto" | "piazza" | "gradescope" | "manual"
    course_id: str
    doc_type: str        # "assignment" | "transcript" | "slide" | "post" | "announcement"
    metadata: dict       # week, lecture_title, due_date, protected, etc.
    embedding: list[float] | None
```

---

## .gitignore (key entries)
```
data/
.env
chroma_db/
kuzu_db/
__pycache__/
*.pyc
.venv/
node_modules/
dashboard/frontend/.next/
```

---

## Dependency Groups

### Core (ingest + process + retrieval)
- `requests`, `playwright` — HTTP + browser scraping
- `pymupdf` — PDF parsing
- `webvtt-py` — .vtt caption file parsing
- `spacy` + `en_core_web_sm` — NER for anonymization
- `sentence-transformers` — HuggingFace embeddings
- `chromadb` — vector store
- `networkx` — graph (prototype); `kuzu` — persistent graph (production)
- `piazza-api` — Piazza scraper
- `pyyaml` — config parsing

### LLM + Chatbot
- `anthropic` — Claude SDK
- `streamlit` — web UI (stretch)

### Dashboard (Phase 3)
- `fastapi`, `uvicorn` — backend
- `sqlalchemy` — ORM for SQLite

### Dev
- `pytest`, `ruff`, `mypy`
