# TODO — Getting Started

## Phase 0: Setup

- [ ] Copy `.env.example` → `.env` and fill in credentials:
  - [ ] `CANVAS_API_TOKEN` — generate at canvas.mit.edu → Account → Settings → New Access Token
  - [ ] `ANTHROPIC_API_KEY`
  - [ ] `PIAZZA_EMAIL` / `PIAZZA_PASSWORD`
  - [ ] `GRADESCOPE_EMAIL` / `GRADESCOPE_PASSWORD`
- [ ] Fill in `config/courses.yaml` with 6.1220 IDs:
  - [ ] `canvas_course_id` — from Canvas course URL
  - [ ] `gradescope_course_id` — from Gradescope course URL
  - [ ] `panopto_folder_id` — from Panopto
  - [ ] `piazza_course_id` — from Piazza network URL
- [ ] Install Python dependencies: `pip install -e ".[dev]"`
- [ ] Download spaCy model: `python -m spacy download en_core_web_sm`
- [ ] Install frontend dependencies: `cd frontend && npm install`

---

## Phase 1: Data Ingestion

- [ ] **Canvas** — `ingest/canvas.py` is implemented, test it:
  ```
  python scripts/run_ingest.py --course 6.1220 --sources canvas
  ```
- [ ] **Manual files** — drop lecture PDFs/slides into `data/manual/6.1220/slides/` and run:
  ```
  python scripts/run_ingest.py --course 6.1220 --sources manual
  ```
- [ ] **Panopto** — implement `ingest/panopto.py`:
  - [ ] Figure out MIT SSO / Panopto API auth
  - [ ] List sessions for the 6.1220 folder
  - [ ] Download `.vtt` caption files per session
  - [ ] Fallback: manually download `.vtt` files and drop in `data/manual/6.1220/`
- [ ] **Piazza** — implement `ingest/piazza.py`:
  - [ ] Test `piazza-api` login with MIT credentials
  - [ ] Fetch all posts + Q&A for 6.1220 network
  - [ ] Confirm anonymizer runs before any content is saved
  - [ ] Fallback: export HTML from Piazza and use `ingest/manual.py`
- [ ] **Gradescope** — implement `ingest/gradescope.py`:
  - [ ] Evaluate `nyuoss/gradescope-api` for session auth
  - [ ] Fetch assignment list, due dates, submission status, scores
  - [ ] Run anonymizer on any feedback content

---

## Phase 2: Processing & RAG

- [ ] Run the full processing pipeline:
  ```
  python scripts/run_process.py --course 6.1220
  ```
- [ ] Verify ChromaDB index is populated (`chroma_db/` directory appears)
- [ ] Test CLI chatbot end-to-end:
  ```
  python chatbot/cli.py 6.1220
  ```
- [ ] Test guardrails:
  - [ ] Ask a concept question → should answer
  - [ ] Ask "solve problem 3" → should be blocked
- [ ] Run test suite: `pytest`

---

## Phase 2 (stretch): GraphRAG

- [ ] Implement graph builder in `retrieval/graph_store.py`:
  - [ ] Extract topic nodes from syllabus using LLM tagger
  - [ ] Link lectures → topics (covers), assignments → topics (assessed_by)
  - [ ] Link Piazza threads → topics (discussed_in)
- [ ] Test `GraphRetriever` and `HybridRetriever`
- [ ] Compare retrieval quality: vector-only vs hybrid

---

## Phase 2: Web UI

- [ ] Start backend: `uvicorn backend.main:app --reload`
- [ ] Start frontend: `cd frontend && npm run dev`
- [ ] Test chat at `http://localhost:3000/chat`
- [ ] Verify SSE streaming works (responses appear token by token)
- [ ] Verify source cards appear below assistant messages

---

## Phase 3 (Optional): Dashboard

- [ ] Populate `backend/routes/assignments.py` from SQLite after ingestion
- [ ] Build out `frontend/app/dashboard/page.tsx` with real data
- [ ] Implement `frontend/components/TopicMap.tsx` (D3 or React Flow)
- [ ] Add calendar view: week-by-week deadlines + lecture topics

---

## Open Questions to Resolve

- [ ] Panopto: direct `.vtt` download links available, or need to reverse-engineer API auth?
- [ ] Guardrail sensitivity: `permissive` (default) vs `conservative` — confirm with professor
- [ ] GraphRAG graph DB: NetworkX in-memory (current) sufficient for demo, or upgrade to KuzuDB?
- [ ] Embedding model: `bge-small` (fast, ~130MB) vs `nomic-embed-text` (better for long docs, ~600MB)?
- [ ] Update cadence: scrape once for prototype, or add a scheduled re-sync script?
