# Agentic AI Document Intelligence & Compliance Checker

Extracts requirements from one or more **reference documents**, audits one or more **submitted documents** against them, and produces an evidence-traceable compliance report: status, requirement matrix, missing / conflicting / deviating information, remarks, evidence locations and a final summary.

**Core rule:** every verdict is tied to a requirement and to a verbatim quote at a known location (document, page, section, line, character range). Missing information is **never** assumed compliant; unverifiable evidence is routed to *Requires Human Review*.

| Deliverable | Where |
|---|---|
| Backend (FastAPI) | `backend/` |
| Frontend (React + TypeScript + Tailwind) | `frontend/` |
| Deployed backend URL (Render) | **TODO: add after deploying** |
| Deployed frontend URL (Vercel) | **TODO: add after deploying** |
| GitHub repository | **TODO: add after pushing** |

---

## Architecture

```
 PDF / DOCX / TXT (multiple, both sides)
        |
   Parser -> Chunker (page / section / line / char offsets)
        |                                   
        |      +--------------------------- per-job vector index ---------------------------+
        +----> | Sentence-Transformers embeddings -> ChromaDB (or FAISS)  +  BM25 + overlap | (hybrid RAG)
               +------------------------------------------------------------------------------+
                                           |
  LangGraph StateGraph (shared ComplianceAgentState)
  1 Classification -> 2 Information Extraction -> 3 Requirement Extraction
        -> 4 Compliance (RAG + evidence rules) -> 5 Discrepancy -> 6 Decision / Reviewer
                                           |
   PostgreSQL (documents, jobs, reports, audit trail)   Redis (agent memory, event log)
                                           |
              React UI: matrix, evidence inspector, findings, overrides, exports
```

### Agents

| # | Agent | Output |
|---|---|---|
| 1 | Document Classification | document type, domain, structure |
| 2 | Information Extraction | sections, tables, values, declarations |
| 3 | Requirement Extraction | atomic `RequirementItem`s (id, severity, category, source document) |
| 4 | Compliance | per-requirement verdict, retrieved passages, verbatim evidence + location |
| 5 | Discrepancy | missing / conflicting / deviating / ambiguous items + remediation |
| 6 | Decision / Reviewer | re-verifies every quote against source text, severity-weighted score, final status, summary |

### Evidence guards (deterministic, in `app/agents/evidence_rules.py`)
* **Explicit omission** – if a submitted document says inspection/material/testing/design evidence is "missing", "pending", "omitted" etc., that exact sentence becomes the citation and the requirement is Non-Compliant. The page/section reported is where the sentence lives, in the document that contains it.
* **Numeric deviation** – if a requirement sets a minimum/maximum (e.g. "exceeding 2.5x", "within 30 business days") and the *only* comparable values in the evidence violate it, the verdict is downgraded and the conflict is listed. Nothing is flagged when no comparable number exists.
* **Reviewer verification** – a Compliant / Partially Compliant verdict whose quote cannot be found verbatim in the submitted text is changed to *Requires Human Review*.

### Technology map (problem statement -> implementation)

| Requirement | Implementation |
|---|---|
| Python + FastAPI, Pydantic, async | `backend/app` |
| Agent framework | **LangGraph** `StateGraph` (`agents/orchestrator.py`); sequential fallback if the package is missing |
| LLM | Gemini / OpenAI / Anthropic via `core/llm_provider.py`, plus an offline deterministic engine (`DEFAULT_LLM_PROVIDER=mock`) |
| PDF/DOCX processing | `pypdf`, `python-docx` (`ingestion/parser.py`) |
| Sentence Transformers | `ingestion/embeddings.py` (default `all-MiniLM-L6-v2`) |
| Vector database | **ChromaDB** (default) or **FAISS** (`VECTOR_BACKEND`), `ingestion/dense_index.py`; one collection per job |
| RAG | hybrid dense + BM25 + token overlap (`ingestion/vector_store.py`) |
| PostgreSQL | SQLAlchemy async + asyncpg (`core/database.py`, `services/persistence.py`) |
| Redis | `core/memory.py` (state, per-job event log; falls back to memory if unreachable) |
| Frontend | React 18, TypeScript, Tailwind, Vite |
| Exports | PDF, CSV, JSON, Markdown |

Graceful degradation: if the embedding model, Chroma/FAISS, Redis or LangGraph is unavailable the app logs a warning and continues (lexical retrieval / in-memory state / sequential agents). `GET /health` and every report's `pipeline_info` show which components were actually used.

---

## Run locally

### Option A – Docker Compose (PostgreSQL + Redis + ChromaDB, closest to production)
```bash
docker compose up --build
```
UI: http://localhost:5173 · API docs: http://localhost:8000/docs · health: http://localhost:8000/health

### Option B – without Docker (SQLite, in-memory state)
```bash
cd backend
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
```bash
cd frontend
npm install
npm run dev                                           # http://localhost:5173 (proxies /api to :8000)
```
Set `EMBEDDING_BACKEND=none` for a fast start without downloading the embedding model (lexical retrieval only).

### Tests
```bash
cd backend && python -m pytest -q
```
Tests are hermetic (no model download, no external services).

---

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/documents/upload` | parse + store one PDF/DOCX/TXT (call repeatedly for multiple); returns extracted text |
| POST | `/api/compliance/analyze` | run the workflow on `reference_documents[]` + `submitted_documents[]` (inline text or stored ids) |
| GET | `/api/compliance/report/{job_id}` | stored report |
| GET | `/api/compliance/events/{job_id}` | agent event log |
| POST | `/api/compliance/override/{job_id}` | human reviewer override (persisted, score/status recomputed) |
| GET | `/api/compliance/reports` | recent audits |
| GET | `/api/export/{job_id}/{pdf\|csv\|json\|markdown}` | exports |
| GET | `/api/samples` | benchmark scenarios |

## Recent fixes
* **Compound requirements are split into atomic ones.** "must contain A, B, C, and D" (or "A and B") now yields one requirement per item (`agents/requirement_splitter.py`), both for the offline engine and for LLM output; `source_clause` keeps the original sentence.
* **Offline engine no longer extracts its own prompt template** as bogus requirements, and its verdicts now come from the evidence heuristic (keyword coverage + verbatim best-matching line) rather than a canned "Partially Compliant".
* **No evidence = Non-Compliant.** Retrieval scores are normalised per query, so they are no longer used as proof of presence.
* **Headings and titles are no longer extracted as requirements** by the offline engine (only lines that state an obligation, or explicit bullets, count), so "SCOPE & APPLICABILITY" no longer appears as a requirement with "No Document Evidence Found".
* More omission phrases detected ("not available", "not yet", "TBD", "to be provided"...).
* Default model names updated (`gemini-2.5-flash`, `claude-sonnet-5-5`); confirm them against your provider's current model list.

## Problem-statement example
Reference: *"The submitted report must contain design calculations, material specifications, inspection requirements, and testing procedures."*
Submitted: design **Available**, material **Available**, inspection **Missing**, testing **Available**.
Expected: inspection requirement = **Non-Compliant / Information Missing**, citing the sentence that says it is missing; the others cite their own supporting quotes; overall status is not *Compliant*. Use **Load multi-document demo** in the UI to see the same case split across two submitted files, with each citation pointing at the correct file.

---

## Deployment

### Backend on Render
1. Push the repo to GitHub.
2. Render -> **New -> Blueprint** -> select the repo. `render.yaml` creates the Docker web service, a PostgreSQL database and a Redis (Key Value) instance and wires `DATABASE_URL` / `REDIS_URL`.
3. Set `CORS_ORIGINS` to your Vercel URL, e.g. `["https://your-app.vercel.app"]` (Vercel preview URLs are already allowed by `CORS_ORIGIN_REGEX`).
4. Optional: add `GEMINI_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` and set `DEFAULT_LLM_PROVIDER`.

Notes: sentence-transformers + PyTorch need more memory than Render's free web tier, hence `plan: starter` in the blueprint. To run on a smaller instance set `EMBEDDING_BACKEND=none`. Please check Render's current Blueprint syntax if the blueprint is rejected (service type names have changed over time).

### Frontend on Vercel
1. Import the repo, **Root Directory = `frontend`**, framework Vite (`npm run build`, output `dist`).
2. Environment variable: `VITE_API_URL=https://<your-render-service>.onrender.com`.

---

## Limitations
* Page numbers are reliable for text-based PDFs only; DOCX/TXT have no stable page layout (offsets and line numbers are still exact against the extracted text).
* Scanned/image-only PDFs need OCR first (the upload is rejected with a clear message).
* A matching quote proves the text exists, not that it technically satisfies the requirement; use the human-review override for high-impact decisions.
* The offline engine is deterministic and rule-based; use an LLM provider for nuanced technical judgement.
* Prototype: needs domain-expert validation and security review before operational use.

See `docs/TRACEABILITY_AND_VALIDATION.md` for the evidence-offset design notes.
#   A g e n t i c _ C o m p l i a n c e _ C h e c k e r  
 