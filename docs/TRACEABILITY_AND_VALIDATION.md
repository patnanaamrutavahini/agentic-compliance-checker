# Step 7 + Step 8: Traceability and final workflow validation

## Step 7 — Evidence source traceability

- Chunks now retain character offsets anchored to the parser's extracted source text rather than estimating line numbers from a fixed character divisor.
- PDF page lookup uses extracted page boundaries supplied by the parser.
- DOCX and TXT physical page numbers cannot be reliably inferred from extracted text; the chunk metadata marks page provenance as not reliable for those formats.
- When the compliance agent has a verbatim evidence snippet, it records exact character and line offsets for that quote in the extracted submission text. Chunk offsets are used only if the quote cannot be found exactly.
- Chunk metadata includes `source_offset_basis`, `source_start_char`, `source_end_char`, and `page_number_reliable`.

**Citation limitation:** Character offsets refer to extracted text, not byte offsets in the original file. PDF page numbers refer to the PDF's extracted page order. DOCX page numbers are not guaranteed because Word pagination depends on layout and rendering. A matching quote proves the quote exists, not that it semantically satisfies a requirement; human review remains important for high-impact decisions.

## Step 8 — Regression validation

New tests exercise the parser → chunker → retrieval path and check that returned evidence retains source coordinates. Run all backend tests from this directory:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
```

If running a focused diagnostic first:

```powershell
python -m pytest -q tests/test_parser.py tests/test_retrieval.py tests/test_reviewer_evidence.py tests/test_traceability_workflow.py
```

The full test suite must be run in the target environment after dependencies are installed. This ZIP was checked in the build environment with the targeted parser/retrieval/agent/reviewer tests; the full suite could not be collected there because `aiosqlite` was not installed in that environment.

## Final local smoke test

1. Start the backend using the project's existing run instructions.
2. Upload or paste a reference document and a submitted document.
3. Run compliance analysis.
4. Inspect a verdict with evidence and verify its quote, `start_char`, `end_char`, and `line_number` against the extracted submitted text.
5. Confirm that missing/unverifiable evidence is routed to human review rather than being presented as proven compliance.

Do not describe the system as production-certified. It is a prototype that requires domain-expert validation, security review, and deployment testing before operational use.
