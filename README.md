# Agentic AI Document Intelligence & Compliance Checker

An evidence-traceable, multi-document compliance auditing application
that compares submitted documents against one or more reference
documents. It produces a compliance report containing requirement-level
verdicts, missing or conflicting information, deviations, remarks,
evidence locations, and a final summary.

**Core principle:** Every verdict must be tied to a specific requirement
and supporting evidence. Evidence should include a verbatim quote and
its source location (document, page, section, line, or character range
where available). Missing information is never assumed to be compliant;
unverifiable evidence is routed to **Requires Human Review**.

## Live Demo

  -------------------------------------------------------------------------------------------------------
  Deliverable                         Link
  ----------------------------------- -------------------------------------------------------------------
  Frontend application                https://agentic-compliance-checker.vercel.app/

  Backend API                         https://compliance-checker-api.onrender.com

  API documentation                   https://compliance-checker-api.onrender.com/docs

  Health check                        https://compliance-checker-api.onrender.com/health

  GitHub repository                   https://github.com/patnanaamrutavahini/agentic-compliance-checker
  -------------------------------------------------------------------------------------------------------

## Key Features

-   Upload multiple reference documents and submitted documents.
-   Supports PDF, DOCX, and TXT documents.
-   Extracts requirements from reference documents and compares them
    with submitted evidence.
-   Uses hybrid retrieval (dense retrieval, BM25, and token overlap) to
    find relevant evidence.
-   Generates a requirement-by-requirement compliance matrix.
-   Identifies missing, conflicting, deviating, and ambiguous
    information.
-   Includes verbatim evidence quotes and source locations when
    available.
-   Re-verifies evidence quotes before finalizing the report.
-   Supports human-review overrides and audit history.
-   Exports reports to PDF, CSV, JSON, and Markdown.
-   Provides a multi-document demo to demonstrate evidence traceability.

## Architecture

``` text
Reference documents + Submitted documents
                  |
        PDF / DOCX / TXT parser
                  |
      Chunking + source-location metadata
                  |
       Hybrid retrieval / RAG layer
       Dense retrieval + BM25 + overlap
                  |
         Compliance agent workflow
                  |
  1. Document Classification
  2. Information Extraction
  3. Requirement Extraction
  4. Evidence-Based Compliance Analysis
  5. Discrepancy Detection
  6. Decision and Reviewer Verification
                  |
    Compliance report + audit trail
                  |
     React user interface and exports
```

## Agent Workflow

  ------------------------------------------------------------------------
                            \# Agent                 Responsibility
  ---------------------------- --------------------- ---------------------
                             1 Document              Identifies document
                               Classification        type, domain, and
                                                     structure.

                             2 Information           Extracts relevant
                               Extraction            sections, tables,
                                                     values, and
                                                     declarations.

                             3 Requirement           Converts reference
                               Extraction            clauses into atomic
                                                     requirements with
                                                     IDs, severity,
                                                     category, and source
                                                     document.

                             4 Compliance Analysis   Retrieves relevant
                                                     passages and
                                                     evaluates each
                                                     requirement against
                                                     available evidence.

                             5 Discrepancy Detection Identifies missing,
                                                     conflicting,
                                                     deviating, or
                                                     ambiguous information
                                                     and suggests
                                                     remediation.

                             6 Decision / Reviewer   Re-verifies evidence
                                                     quotes, calculates a
                                                     severity-weighted
                                                     score, and prepares
                                                     the final status and
                                                     summary.
  ------------------------------------------------------------------------

## Evidence and Decision Rules

-   **Explicit omission:** If a submitted document explicitly says that
    required inspection, material, testing, design, or other evidence is
    missing, pending, omitted, or not yet available, that statement can
    be cited as evidence of non-compliance.
-   **Numeric deviation:** Where a requirement specifies a minimum or
    maximum, comparable evidence values are checked for violations. A
    deviation is flagged only when comparable values are available.
-   **Quote verification:** If a Compliant or Partially Compliant
    verdict relies on a quote that cannot be found verbatim in the
    submitted text, the verdict is changed to **Requires Human Review**.
-   **Missing evidence:** The absence of evidence is not treated as
    proof of compliance.
-   **Human review:** A matching quote establishes that text exists; it
    does not necessarily prove that the requirement has been technically
    satisfied.

## Technology Stack

  -----------------------------------------------------------------------
  Area                                Technologies
  ----------------------------------- -----------------------------------
  Backend API                         Python, FastAPI, Pydantic

  Agent orchestration                 LangGraph StateGraph, with
                                      sequential fallback

  LLM providers                       Gemini, OpenAI, Anthropic, or
                                      deterministic offline/mock mode

  Document parsing                    pypdf, python-docx

  Embeddings                          Sentence Transformers
                                      (`all-MiniLM-L6-v2` by default)

  Vector search                       ChromaDB or FAISS

  Retrieval                           Hybrid RAG: dense retrieval, BM25,
                                      and token overlap

  Persistence                         SQLAlchemy async, asyncpg,
                                      PostgreSQL

  Agent memory / events               Redis with in-memory fallback

  Frontend                            React 18, TypeScript, Tailwind CSS,
                                      Vite

  Report exports                      PDF, CSV, JSON, Markdown
  -----------------------------------------------------------------------

The application is designed to degrade gracefully if optional components
such as embeddings, ChromaDB/FAISS, Redis, or LangGraph are unavailable.
The health endpoint and each report's `pipeline_info` indicate which
components were actually used.

## Project Structure

``` text
Agentic_Compliance_Checker/
├── backend/
│   └── app/
│       ├── agents/
│       ├── ingestion/
│       ├── core/
│       ├── services/
│       └── main.py
├── frontend/
├── docs/
│   └── TRACEABILITY_AND_VALIDATION.md
├── docker-compose.yml
└── render.yaml
```

*The exact directory contents may vary by repository version.*

## Run Locally

### Option A: Docker Compose

Start the configured services:

``` bash
docker compose up --build
```

When running locally, the expected URLs are:

-   Frontend: http://localhost:5173
-   Backend API: http://localhost:8000
-   API documentation: http://localhost:8000/docs
-   Health check: http://localhost:8000/health

### Option B: Run Without Docker

#### 1. Start the backend

``` bash
cd backend
python -m venv venv
```

Activate the virtual environment:

``` powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

``` bash
# macOS / Linux
source venv/bin/activate
```

Install dependencies and configure the environment:

``` bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and update the settings as needed. Then
run:

``` bash
uvicorn app.main:app --reload --port 8000
```

#### 2. Start the frontend

Open another terminal:

``` bash
cd frontend
npm install
```

Create or update the frontend environment file if required:

``` env
VITE_API_URL=https://compliance-checker-api.onrender.com
```

For local development, set `VITE_API_URL` to `http://localhost:8000` if
the frontend configuration expects the backend base URL directly.
Restart the Vite server after changing environment variables.

Run the frontend:

``` bash
npm run dev
```

### Optional: Faster Local Startup

If you want to avoid downloading the embedding model, set:

``` env
EMBEDDING_BACKEND=none
```

This uses lexical retrieval only, where supported by the current
configuration.

## API Endpoints

  -------------------------------------------------------------------------------------
  Method                  Endpoint                              Purpose
  ----------------------- ------------------------------------- -----------------------
  `POST`                  `/api/documents/upload`               Upload and parse a PDF,
                                                                DOCX, or TXT document.
                                                                Repeat for multiple
                                                                documents.

  `POST`                  `/api/compliance/analyze`             Run the workflow
                                                                against reference and
                                                                submitted documents.

  `GET`                   `/api/compliance/report/{job_id}`     Retrieve a stored
                                                                compliance report.

  `GET`                   `/api/compliance/events/{job_id}`     Retrieve the agent
                                                                event log.

  `POST`                  `/api/compliance/override/{job_id}`   Apply a human-review
                                                                override and recompute
                                                                status/score.

  `GET`                   `/api/compliance/reports`             List recent audits.

  `GET`                   `/api/export/{job_id}/{format}`       Export a report as PDF,
                                                                CSV, JSON, or Markdown.

  `GET`                   `/api/samples`                        Retrieve sample
                                                                benchmark scenarios.

  `GET`                   `/health`                             Check backend health
                                                                and active components.
  -------------------------------------------------------------------------------------

For the interactive API schema, visit the [deployed API
documentation](https://compliance-checker-api.onrender.com/docs).

## Example Scenario

**Reference requirement:**

> The submitted report must contain design calculations, material
> specifications, inspection requirements, and testing procedures.

**Submitted evidence:**

-   Design calculations: Available
-   Material specifications: Available
-   Inspection requirements: Missing
-   Testing procedures: Available

**Expected result:** The inspection requirement should be marked
**Non-Compliant / Information Missing**, with a citation to the
submitted document's statement indicating that the information is
missing. The other requirements should cite their own supporting
evidence. The overall report must not be marked Compliant while a
required item remains unsatisfied.

Use **Load multi-document demo** in the interface to explore a similar
case across multiple submitted files.

## Tests

Run the backend tests from the backend directory:

``` bash
cd backend
python -m pytest -q
```

The test suite is intended to run without downloading models or
requiring external services.

## Deployment

### Backend --- Render

The backend is deployed at:

https://compliance-checker-api.onrender.com

The API documentation is available at:

https://compliance-checker-api.onrender.com/docs

If redeploying with a Render Blueprint, review the environment variables
and service configuration in `render.yaml`. Configure `CORS_ORIGINS` to
include the deployed frontend origin:

``` text
https://agentic-compliance-checker.vercel.app
```

LLM API keys are optional when using the deterministic mock/offline
provider. If using an external LLM provider, configure the corresponding
secret in Render and select the provider through the project's
environment settings. Never commit API keys or secrets to GitHub.

### Frontend --- Vercel

The frontend is deployed at:

https://agentic-compliance-checker.vercel.app/

For a Vite frontend, set the Vercel project root directory to `frontend`
and configure the production API base URL as:

``` env
VITE_API_URL=https://compliance-checker-api.onrender.com
```

Confirm that the frontend code uses `VITE_API_URL` for API requests and
that the backend CORS configuration permits the deployed frontend
origin.

## Limitations

-   Page numbers are most reliable for text-based PDFs. DOCX and TXT
    files do not have a stable page layout; offsets and line numbers
    refer to extracted text.
-   Scanned or image-only PDFs require OCR before processing.
-   A matching quote proves that the text exists, not that it
    technically satisfies the requirement.
-   The offline engine is deterministic and rule-based. Nuanced
    technical judgments may require an LLM provider and human review.
-   This is a prototype and should undergo domain-expert validation and
    a security review before operational use.

For more details about evidence offsets and traceability, see
[`docs/TRACEABILITY_AND_VALIDATION.md`](docs/TRACEABILITY_AND_VALIDATION.md).

## Recent Improvements

-   Splits compound requirements into atomic items.
-   Prevents prompt-template text and ordinary headings from being
    treated as requirements by the offline engine.
-   Uses evidence heuristics and verbatim matching instead of a canned
    partial-compliance verdict.
-   Treats missing evidence as non-compliant rather than relying on
    retrieval scores as proof.
-   Detects additional omission phrases such as "not available," "not
    yet," "TBD," and "to be provided."
-   Re-verifies supporting quotes before finalizing verdicts.

------------------------------------------------------------------------

## Author

**Amrutha Patnana**

Project: **Agentic AI Document Intelligence & Compliance Checker**

-   [GitHub
    Repository](https://github.com/patnanaamrutavahini/agentic-compliance-checker)
-   [Live Frontend](https://agentic-compliance-checker.vercel.app/)
-   [Live Backend API](https://compliance-checker-api.onrender.com)
