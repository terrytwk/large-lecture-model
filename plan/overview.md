# Large Lecture Model (LLM) — Project Plan

A study and assignment organization tool for college students, powered by LLM and RAG over course materials.

---

## Vision

Pull all course content and activity from Canvas, Gradescope, Panopto, and Piazza into a unified knowledge base, then expose it through a chatbot and (optionally) a dashboard. A student should be able to ask "What topics does PS3 cover and where are the relevant lecture slides?" and get a grounded answer.

Prototype target: **MIT 6.1220** (single course). All scripts should be parameterized to generalize to any course.

---

## Architecture Overview

```
[Data Sources]        [Ingestion]     [Processing]       [Knowledge Layer]     [Interface]

Canvas ──────────┐                   chunker
Gradescope ──────┤──> scrapers/ ──>  anonymizer  ──>  vector DB (ChromaDB)  ──> chatbot CLI
Panopto ─────────┤                   embedder          graph DB (KuzuDB)        (optional) web UI
Piazza ──────────┘                   tagger       ──>  hybrid retriever     ──> dashboard
(+ manual HTML)                                        
                                         │
                                    guardrails layer
                                  (academic integrity)
```

---

## Key Constraints & Considerations

### Privacy & PII (Piazza, Gradescope)
- Piazza posts contain student names, email handles, and sometimes personal details
- **Anonymization is required before any content enters the knowledge base**
- Strategy: regex + NER pass strips names/emails; replace with tokens (Student_A, Student_B)
- Raw scraped data is stored in `data/raw/` (gitignored); only anonymized versions go into `data/processed/`
- Peer grading feedback from Gradescope should also be anonymized
- No student PII ever enters the vector DB, graph, or LLM context

### Academic Integrity Guardrails
- Professor concern: LLM should not directly answer pset or exam questions
- Strategy: multi-layer guardrail system
  1. **Tagging at ingest**: each assignment/exam is tagged as `protected: true` in metadata
  2. **Query classifier**: pre-filter that detects "solve this problem" intent before retrieval
  3. **System prompt constraint**: LLM instructed to explain concepts and point to resources, never to produce solutions
  4. **Configurable**: `config/courses.yaml` lets instructor mark which assignments are protected and during what window
- Allowed: "explain the concept behind PS3 Q2", "find relevant lecture slides for topic X", "when is PS3 due"
- Blocked: "solve PS3 Q2", "give me the answer to", "write the code for problem 3"

---

## Phase 1 — Data Ingestion

Goal: pull raw content from each platform into structured local files.

### 1a. Canvas
- **Auth**: OAuth2 token (stored in `.env`)
- **API**: official Canvas REST API
- **Collect**: syllabus, assignments (name, due date, description, points), announcements, course files (PDFs, slides), grades
- **Output**: `data/raw/canvas/{course_id}/`

### 1b. Gradescope
- **Auth**: email/password session cookie (no official API)
- **Reference**: [nyuoss/gradescope-api](https://github.com/nyuoss/gradescope-api) as starting point
- **Collect**: assignment list, due dates, submission status, scores, rubric/feedback
- **Output**: `data/raw/gradescope/{course}/`
- **Note**: feedback PDFs may contain student names — run anonymizer before processing

### 1c. Panopto
- **Auth**: access via MIT SSO / direct download links
- **Collect**: lecture video list, **transcript/caption files** (.vtt) — transcripts are the primary artifact
- **Strategy**: script to download `.vtt` caption files; optionally download video for future audio processing
- **Output**: `data/raw/panopto/{course}/transcripts/`

### 1d. Piazza
- **Auth**: email/password via `piazza-api` Python library
- **Collect**: all posts, instructor answers, student Q&A, tags
- **Fallback**: if API is tricky, accept manually exported HTML files from Piazza's export feature
- **Anonymization**: immediately on ingest, before writing to disk
- **Output**: `data/raw/piazza/{course}/` (anonymized only — never store raw with PII)

### 1e. Manual / Supplemental
- Accept manually provided files: slides PDFs, notes, exported HTML
- Drop into `data/manual/` and the pipeline picks them up automatically

---

## Phase 2 — Content Processing

Goal: transform raw content into indexed, retrievable chunks.

### 2a. Chunking Strategy
| Source | Chunk unit | Metadata |
|---|---|---|
| PDF slides | per slide (or per page) | course, week, lecture title, page# |
| Transcripts | 5-min segments | course, week, lecture title, start_time |
| Piazza posts | per thread (Q + answers) | course, tags, anonymized |
| Assignments | full description | course, due_date, protected flag |
| Announcements | full text | course, date |

### 2b. Anonymization (`process/anonymizer.py`)
- Runs on Piazza and Gradescope content
- Uses regex for emails/student IDs + spaCy NER for person names
- Replaces identified entities with stable pseudonyms within a session (Student_A, Student_B)
- Logs what was stripped (without the actual PII) for auditability

### 2c. Embeddings
- **Model**: HuggingFace open-source — `BAAI/bge-small-en-v1.5` (fast, good quality) or `nomic-ai/nomic-embed-text-v1` (longer context)
- Runs locally via `sentence-transformers` — no API cost, works offline
- Embedder is abstracted behind an interface so model can be swapped

### 2d. Topic Tagging
- LLM pass over assignments and lecture titles to extract topic labels (e.g., "dynamic programming", "graph algorithms")
- Tags stored in metadata — used to build graph edges and power dashboard topic mapping

---

## Phase 2 — Knowledge Layer & Retrieval

Two retrieval backends, both implemented and selectable:

### Vector Retrieval (default, simpler)
- **DB**: ChromaDB (local, no server needed)
- Cosine similarity search over embedded chunks
- Filter by metadata: `course`, `source`, `type`, `protected`

### GraphRAG (stretch, but planned)
- **DB**: KuzuDB (embedded graph DB) or NetworkX for prototype
- **Graph structure**:
  - Nodes: topics/concepts, lectures, assignments, Piazza threads
  - Edges: "covers topic", "assessed by", "prerequisite of", "discussed in"
- **Build**: LLM extracts relationships from syllabus + assignment descriptions at ingest
- **Query**: graph traversal augments vector retrieval — e.g., find pset → find topics it covers → find lectures covering those topics
- **Why it's powerful**: lets students navigate "what do I need to review to tackle PS5" across all content types

### Hybrid Retriever (`retrieval/hybrid_retriever.py`)
- Combines both: vector search for semantic similarity, graph traversal for structured navigation
- Application layer can choose which retriever to use per query type
- Modularity: each retriever behind a common interface (`BaseRetriever`)

---

## Phase 2 — Chatbot

### Pipeline
1. Query → guardrail classifier (block if pset-solving intent detected)
2. Query → embed → vector/graph retrieval → top-k chunks
3. Chunks + query → LLM with system prompt + tool access
4. Response with citations (source, lecture name, slide page, etc.)

### LLM
- Anthropic Claude via SDK (with tool use)
- Tools: `search_materials`, `get_assignment_details`, `get_deadlines`, `get_lecture_transcript`

### Interfaces
- v1: CLI REPL (`chatbot/cli.py`)
- v2: Streamlit web app (`chatbot/app.py`)

---

## Phase 3 (Optional) — Dashboard

- **Assignment tracker**: all psets/exams, due dates, submission status, scores
- **Topic mapping**: each assignment → topics → linked lecture clips and slides
- **Calendar view**: week-by-week deadlines + what was covered
- **Review mode**: click assignment → see recommended lectures/notes
- **Stack**: Next.js + Tailwind frontend, FastAPI backend, SQLite for structured data

---

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Scrapers | Python + `requests` | per-source scripts |
| Browser scraping | `playwright` (if needed) | Gradescope fallback |
| PDF parsing | `pymupdf` | fast, handles most course PDFs |
| Anonymization | `spacy` + regex | NER for person names |
| Embeddings | `sentence-transformers` (HuggingFace) | local, no API cost |
| Embedding model | `BAAI/bge-small-en-v1.5` | swap-able via config |
| Vector DB | ChromaDB (local) | upgrade path to Pinecone |
| Graph DB | NetworkX → KuzuDB | for GraphRAG |
| LLM | Claude (Anthropic SDK) | with tool use + guardrails |
| Chatbot UI | Next.js + FastAPI (streaming) | replaces Streamlit |
| Dashboard | Next.js (same app, /dashboard route) | Phase 3 |

---

## Build Order

```
Phase 0  [ ] repo scaffold, pyproject.toml, .env.example, data/ dirs
Phase 1  [ ] Canvas scraper (1a)
         [ ] Panopto transcript downloader (1c)
         [ ] Piazza scraper + anonymizer (1d)
         [ ] Gradescope scraper (1b)
Phase 2  [ ] PDF chunker + transcript chunker (2a)
         [ ] HuggingFace embedder + ChromaDB indexer (2b-c)
         [ ] Vector retriever + CLI chatbot (RAG pipeline)
         [ ] Guardrails layer (academic integrity)
         [ ] GraphRAG: graph builder + graph retriever (stretch)
         [ ] Hybrid retriever
         [ ] Streamlit web UI (stretch)
Phase 3  [ ] Dashboard (optional)
```

---

## Open Questions

1. **Panopto access**: do you have direct .vtt download links, or do we need to reverse-engineer the Panopto API to list sessions?
2. **Guardrail sensitivity**: should the classifier block questions that _mention_ a pset (conservative) or only questions that clearly ask for solutions (permissive)?
3. **Graph complexity**: for GraphRAG prototype, is NetworkX (in-memory, no persistence) enough, or should we go straight to KuzuDB?
4. **Update cadence**: scrape once manually for prototype, or add a scheduled re-sync?
5. **Embedding tradeoff**: `bge-small` (fast, ~130MB) vs `nomic-embed-text` (better for long docs, ~600MB) — preference?
