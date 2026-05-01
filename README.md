# Large Lecture Model (LLM)

An AI-powered study assistant for college courses. Scrapes course content from Canvas, Gradescope, Panopto, and Piazza, indexes it into a vector knowledge base, and exposes a chatbot that can answer questions, summarize lectures, and surface deadlines — without solving your problem sets for you.

Built for MIT 6.1220 (Design and Analysis of Algorithms), but designed to work with any course.

---

## How it works

```text
Canvas / Piazza / Panopto / Gradescope
        ↓  ingest
  data/raw/{source}/{course}/documents.jsonl
        ↓  chunk + embed (local HuggingFace model)
  ChromaDB vector store          Neo4j graph (concepts + prerequisites)
        ↓                               ↓
        └──────── hybrid retrieval ─────┘
                        ↓
          Claude (API or claude -p CLI)
                        ↓
          Chat UI  /  CLI chatbot  /  Topic Map
```

1. **Ingest** — scrape course content into raw JSON documents
2. **Process** — chunk documents, embed with `BAAI/bge-small-en-v1.5` (local, no API cost), index into ChromaDB
3. **Build graph** — use Claude to tag lectures and assignments with algorithmic topics, infer prerequisite relationships, and store as a Neo4j knowledge graph
4. **Chat** — hybrid retrieval combines vector similarity with graph traversal (topic expansion + prerequisite walking), then passes results to Claude with guardrails that block direct problem-solving

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd large-lecture-model

python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
python -m spacy download en_core_web_sm
```

### 2. Configure credentials

```bash
cp .env.example .env
```

Open `.env` and fill in the values you need (see the sections below).

### 3. Start Neo4j

The knowledge graph requires a running Neo4j instance. The easiest way is Docker:

```bash
docker run -d \
  --name neo4j-llm \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/yourpassword \
  neo4j:5
```

Then set your password as an environment variable (or add it to `.env`):

```bash
export NEO4J_PASSWORD=yourpassword
```

Open [http://localhost:7474](http://localhost:7474) to explore the graph visually via Neo4j Browser.

### 4. Configure your course

Edit `config/courses.yaml`:

```yaml
courses:
  "6.1220":
    canvas_course_id: "37219"   # from the Canvas course URL
    ...
```

---

## Getting your Canvas API token

1. Go to [canvas.mit.edu](https://canvas.mit.edu) (or your institution's Canvas URL)
2. Click your profile picture → **Account** → **Settings**
3. Scroll down to **Approved Integrations**
4. Click **+ New Access Token**
5. Give it a name (e.g. `large-lecture-model`) and an expiry date
6. Copy the token — it's only shown once
7. Paste it into `.env`:

```text
CANVAS_API_TOKEN=7867~xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

To find your **canvas_course_id**: open the course in Canvas and look at the URL — it's the number after `/courses/`:

```text
https://canvas.mit.edu/courses/37219
                                ^^^^^
                          canvas_course_id
```

---

## LLM backend

The chatbot works with or without an Anthropic API key:

| Scenario | What happens |
| --- | --- |
| `ANTHROPIC_API_KEY` is set in `.env` | Uses the Anthropic API directly (fastest, supports prompt caching) |
| No API key | Falls back to `claude -p` CLI (requires [Claude Code](https://claude.ai/code) to be installed and logged in) |

To use the API, add to `.env`:

```text
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Getting your Panopto session cookie

The Panopto ingestor authenticates using your browser session cookie — no OAuth app registration needed.

1. Open any lecture recording at [mit.hosted.panopto.com](https://mit.hosted.panopto.com) and log in via MIT SSO
2. Open DevTools → **Application** → **Storage** → **Cookies** → `mit.hosted.panopto.com`
3. Find the key `.ASPXAUTH` and copy its **Value**
4. Add to `.env`:

```text
PANOPTO_COOKIE=.ASPXAUTH=<value>
```

Also set `panopto_folder_id` in `config/courses.yaml`. To find it:

1. Navigate to the course's Panopto folder in your browser
2. Copy the UUID from the URL:

```text
https://mit.hosted.panopto.com/Panopto/Pages/Sessions/List.aspx#folderID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
                                                                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                                           panopto_folder_id
```

### Manual fallback (no cookie)

If you'd rather not extract a cookie, download captions manually with the helper script from `../graphRAG/download_panopto.py`:

```bash
# Get the session ID from the Panopto viewer URL: ?id=<session-id>
python ../graphRAG/download_panopto.py \
  --session-id <UUID> \
  --cookie ".ASPXAUTH=<value>" \
  --duration 0   # full download
```

Then place the resulting `captions.srt` files in:

```text
data/manual/6.1220/panopto/<Lecture Title>.srt
```

The ingestor picks them up automatically on the next run.

---

## Running the pipeline

### Ingest from Canvas

```bash
python scripts/run_ingest.py --course 6.1220 --sources canvas
```

This downloads lecture notes, slides, cliff notes, recitation notes, practice problems, problem sets, past quizzes, and course announcements as searchable text.

### Ingest Panopto transcripts

```bash
python scripts/run_ingest.py --course 6.1220 --sources panopto
```

Fetches captions for every session in the configured folder (requires `PANOPTO_COOKIE` and `panopto_folder_id`). Also automatically picks up any `.srt` / `.vtt` files in `data/manual/6.1220/panopto/`.

### Process and index

```bash
python scripts/run_process.py --course 6.1220
```

Downloads the embedding model on first run (~130 MB), chunks all documents, and indexes them into ChromaDB. Takes 3–5 minutes on CPU.

### Run both in sequence

```bash
python scripts/run_pipeline.py --course 6.1220
```

### Build the knowledge graph

After ingesting and processing, populate the Neo4j graph with course concepts, lecture topics, and prerequisite relationships:

```bash
NEO4J_PASSWORD=yourpassword python scripts/build_graph.py --course-id 6.1220
```

Omit `--course-id` to build graphs for all courses in `courses.yaml`. This calls the LLM to tag each lecture and assignment with topics, then infers prerequisite edges — takes a few minutes on first run. Re-running is safe (all writes use `MERGE`).

Once built, explore the graph at [http://localhost:7474](http://localhost:7474) or via the Topic Map in the dashboard.

---

## Chatbot

### CLI

```bash
python chatbot/cli.py 6.1220
```

### Web UI

```bash
# Terminal 1 — backend
uvicorn backend.main:app --reload

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000/chat](http://localhost:3000/chat).

---

## Academic integrity guardrails

The chatbot will refuse to directly solve problem sets or exams. It will explain concepts, point to relevant lecture material, and help you understand — but not hand you answers.

Sensitivity is configured in `config/settings.yaml`:

```yaml
guardrails:
  sensitivity: "permissive"   # or "conservative"
```

Protected assignment names are listed in `config/courses.yaml`.

---

## Project structure

```text
ingest/         scrapers (Canvas implemented; Gradescope, Panopto, Piazza stubs)
process/        chunker, embedder, anonymizer, tagger, graph_builder
retrieval/      vector store, Neo4j store, graph retriever, hybrid retriever
llm/            Claude client, guardrails, prompts
chatbot/        CLI REPL
backend/        FastAPI server (chat, assignments, materials, graph routes)
frontend/       Next.js 14 web UI
scripts/        run_ingest.py, run_process.py, run_pipeline.py, build_graph.py
config/         courses.yaml, settings.yaml
data/           raw scraped docs (gitignored)
chroma_db/      vector index (gitignored)
plan/           architecture docs and todo list
tests/          pytest suite
```

---

## Adding a new course

1. Add an entry to `config/courses.yaml` with the course's Canvas (and optionally Gradescope/Piazza/Panopto) IDs
2. Run `python scripts/run_pipeline.py --course <course_id>`
3. Run `NEO4J_PASSWORD=... python scripts/build_graph.py --course-id <course_id>`
4. Start the chatbot with `python chatbot/cli.py <course_id>`

---

## Tech stack

| Layer | Technology |
| --- | --- |
| Scraping | Canvas REST API, `requests` |
| PDF extraction | PyMuPDF |
| Embeddings | `BAAI/bge-small-en-v1.5` via `sentence-transformers` |
| Vector DB | ChromaDB (local, persistent) |
| Graph DB | Neo4j 5 (Docker or Desktop) |
| Graph RAG | Neo4j Cypher + vector hybrid retrieval |
| LLM | Claude (Anthropic API or `claude -p` CLI) |
| Backend | FastAPI + SSE streaming |
| Frontend | Next.js 14, Tailwind CSS |
| PII anonymization | spaCy NER + regex |
