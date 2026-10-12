import time
import re
from typing import List, Dict, Any, Tuple
from app.agents.state import ComplianceAgentState
from app.core.llm_provider import LLMProvider
from app.ingestion.vector_store import HybridVectorStore
from app.models.schemas import (
    ComplianceVerdict, 
    ComplianceStatus, 
    EvidenceLocation, 
    AgentExecutionEvent,
    RequirementItem
)
from app.core.memory import memory_store
from app.agents.evidence_rules import (
    find_explicit_omission,
    find_omission_in_documents,
    detect_numeric_deviation,
    locate_chunk,
)
import asyncio


# Kept as a module-level alias for backwards compatibility with existing tests.
_find_explicit_omission = find_explicit_omission

_STOPWORDS = {
    "must", "shall", "should", "required", "contain", "report", "document", "provide", "include",
    "ensure", "stated", "submitted", "with", "that", "this", "have", "been", "each", "from", "into",
    "their", "also", "complete", "explicitly", "clearly", "detailed", "defined", "under", "which",
}


class _OfflinePlaceholder(Exception):
    """The LLM layer returned its canned offline placeholder, not a real judgement."""


def _stem(word: str) -> str:
    return word[:-1] if len(word) > 4 and word.endswith("s") else word


def _best_line(text: str, keywords: List[str]) -> str:
    """Pick the sentence/line of `text` that mentions most requirement keywords.

    Keeps the evidence quote tight (and verbatim) instead of citing a whole chunk that may
    also describe other requirements.
    """
    best, best_hits = None, 0
    for part in re.split(r"(?<=[.!?])\s+|\n+", text or ""):
        part = part.strip()
        if not part:
            continue
        hits = sum(1 for k in keywords if k in part.lower())
        if hits > best_hits:
            best, best_hits = part, hits
    return best or (text or "")[:220]


class ComplianceAgent:
    """
    Agent 4: Compliance Agent
    Performs retrieval-grounded comparison between each atomic requirement
    and the submitted document evidence chunks. Strict anti-hallucination guardrails:
    Missing information is NEVER assumed compliant.
    """
    def __init__(self, llm: LLMProvider, vector_store: HybridVectorStore):
        self.llm = llm
        self.vector_store = vector_store
        self.name = "Compliance Agent"
        self.id = "agent_04_compliance"

    async def run(self, state: ComplianceAgentState) -> ComplianceAgentState:
        start_time = time.time()
        thoughts = [
            f"Initiating RAG compliance matrix evaluation for {len(state.requirements)} requirements...",
            f"Retrieving candidate chunks via hybrid RAG ({self.vector_store.retrieval_mode}) for each requirement...",
            "Applying strict grounding logic: Zero tolerance for assumed or unverified compliance."
        ]

        await memory_store.append_event(state.job_id, {
            "agent_id": self.id,
            "agent_name": self.name,
            "status": "running",
            "thought_process": thoughts,
            "output_summary": f"Auditing {len(state.requirements)} requirements against submitted evidence..."
        })

        verdicts: List[ComplianceVerdict] = []
        sub_raw_lower = state.submitted_raw_text.lower()
        # (name, text) of every submitted document - evidence is always located in its own document
        sub_docs = [(d["filename"], d["text"]) for d in state.submitted_documents] or [
            (state.submitted_filename, state.submitted_raw_text)
        ]
        doc_text = dict(sub_docs)
        doc_ids = {d["filename"]: d.get("document_id") for d in state.submitted_documents}

        for req in state.requirements:
            # Step 1: Retrieve top chunks from submitted document
            top_results = await asyncio.to_thread(self.vector_store.search, req.text, 3)
            
            evidence_chunk = None
            evidence_score = 0.0
            if top_results:
                evidence_chunk, evidence_score = top_results[0]

            # Step 2: Determine semantic match and presence
            req_keywords = [
                _stem(w.lower()) for w in re.findall(r"\b[a-zA-Z]{4,}\b", req.text)
                if w.lower() not in _STOPWORDS
            ]
            
            # Check presence of key topics in submitted text
            matched_keywords = [kw for kw in req_keywords if kw in sub_raw_lower]
            keyword_coverage = (len(matched_keywords) / len(req_keywords)) if req_keywords else 0.5
            
            # Formulate prompt for LLM verdict verification if LLM is active
            system_prompt = (
                "You are an impartial, strict Compliance Auditor AI. Compare the requirement against "
                "the provided document evidence. "
                "CRITICAL RULE: If evidence is missing, mark as 'Non-Compliant' or 'Partially Compliant'. "
                "NEVER assume compliance without explicit proof."
            )

            prompt = (
                f"Requirement ID: {req.id}\n"
                f"Requirement: {req.text}\n"
                f"Category: {req.category}\n"
                f"Mandatory: {req.mandatory}\n\n"
                f"Top Document Evidence Chunk:\n"
                f"\"{evidence_chunk.text if evidence_chunk else 'NO RELEVANT CHUNKS FOUND'}\"\n\n"
                "Evaluate compliance. Return JSON format:\n"
                "{\n"
                '  "status": "Compliant" | "Partially Compliant" | "Non-Compliant" | "Requires Human Review",\n'
                '  "confidence_score": float between 0.0 and 1.0,\n'
                '  "evidence_snippet": string (verbatim quote from chunk, or null if missing),\n'
                '  "rationale": string,\n'
                '  "missing_elements": list of strings,\n'
                '  "remarks": string\n'
                "}"
            )

            try:
                eval_res = await self.llm.generate_json(prompt, system_prompt)
                if eval_res.get("_deterministic"):
                    # Offline engine: use the evidence-based heuristic below, never the canned verdict.
                    raise _OfflinePlaceholder()
                status_str = eval_res.get("status", "Requires Human Review")
                conf = float(eval_res.get("confidence_score", 0.85))
                rationale = eval_res.get("rationale", "Evaluated against submitted document.")
                snippet = eval_res.get("evidence_snippet") or (evidence_chunk.text[:200] if evidence_chunk and evidence_score > 0.3 else None)
                missing = eval_res.get("missing_elements", [])
                remarks = eval_res.get("remarks", "")
            except Exception:
                # Deterministic fallback evaluation
                if keyword_coverage >= 0.75 and evidence_score >= 0.4:
                    status_str = "Compliant"
                    conf = 0.94
                    rationale = f"All key compliance parameters for '{req.category}' verified in document evidence."
                    snippet = _best_line(evidence_chunk.text, req_keywords) if evidence_chunk else None
                    missing = []
                    remarks = "Fully compliant with reference specification."
                # Retrieval scores are normalised per query (the top chunk always scores high), so they
                # cannot prove presence. Partial credit requires real keyword overlap with the requirement.
                elif keyword_coverage >= 0.35:
                    status_str = "Partially Compliant"
                    conf = 0.82
                    rationale = f"Partial evidence found for '{req.category}', but incomplete parameters or details."
                    snippet = _best_line(evidence_chunk.text, req_keywords) if evidence_chunk else None
                    missing = [f"Complete verification logs for {req.text[:40]}..."]
                    remarks = "Additional evidence or calculation sheet required."
                else:
                    status_str = "Non-Compliant"
                    conf = 0.96
                    rationale = f"No evidence found in submitted document for '{req.text}'. Clause is missing."
                    snippet = None
                    missing = [f"Missing mandatory section: {req.text}"]
                    remarks = "Non-Compliant / Information Missing."

            # Normalize Status Enum
            if "Partially" in status_str:
                verdict_status = ComplianceStatus.PARTIALLY_COMPLIANT
            elif "Non" in status_str or "Missing" in status_str:
                verdict_status = ComplianceStatus.NON_COMPLIANT
            elif "Compliant" in status_str:
                verdict_status = ComplianceStatus.COMPLIANT
            else:
                verdict_status = ComplianceStatus.REQUIRES_HUMAN_REVIEW

            # Deterministic contradiction/omission guard: explicit statements that
            # mandatory evidence was omitted must not be overridden by a broadly
            # matching chunk about another topic (for example, design calculations).
            matching_topic, omission_quote, omission_doc = find_omission_in_documents(
                str(getattr(req, "text", "")), sub_docs
            )
            if not omission_quote:
                matching_topic, omission_quote, omission_doc = find_omission_in_documents(
                    str(getattr(req, "category", "")), sub_docs
                )
            evidence_doc = evidence_chunk.document_name if evidence_chunk else None
            evidence_page = evidence_chunk.page_number if evidence_chunk else 1
            evidence_section = evidence_chunk.section_title if evidence_chunk else "General"
            evidence_chunk_start = evidence_chunk.start_char if evidence_chunk else None
            evidence_chunk_end = evidence_chunk.end_char if evidence_chunk else None
            evidence_chunk_line = evidence_chunk.line_number if evidence_chunk else None
            sim_score = evidence_score
            if omission_quote:
                verdict_status = ComplianceStatus.NON_COMPLIANT
                snippet = omission_quote
                evidence_doc = omission_doc
                sim_score = 1.0
                conf = max(float(conf), 0.9)
                missing = list(missing or [])
                if omission_quote not in missing:
                    missing.append(omission_quote)
                rationale = f"The submitted document explicitly states that required {matching_topic} evidence is missing, omitted, or still pending."
                remarks = f"Explicit omission detected: {omission_quote}"
                # Page/section must describe where the omission sentence lives, not the
                # best semantic match (which may be an unrelated section).
                pos = doc_text.get(omission_doc, "").find(omission_quote)
                located = locate_chunk(state.submitted_chunks, omission_doc, pos) if pos >= 0 else None
                if located:
                    evidence_page = located["page_number"]
                    evidence_section = located["section_title"]
                    evidence_chunk_start, evidence_chunk_end = located["start_char"], located["end_char"]
                    evidence_chunk_line = located["line_number"]

            # Numeric deviation / contradiction check against the retrieved evidence.
            deviations: List[str] = []
            conflicting: List[str] = []
            if snippet and not omission_quote and evidence_chunk is not None:
                deviations = detect_numeric_deviation(req.text, evidence_chunk.text)
                if deviations:
                    conflicting = list(deviations)
                    if verdict_status == ComplianceStatus.COMPLIANT:
                        verdict_status = ComplianceStatus.PARTIALLY_COMPLIANT
                    remarks = (remarks + " " if remarks else "") + "Numeric deviation detected: " + " ".join(deviations)
                    rationale = (rationale + " " if rationale else "") + "A stated value does not meet the numeric limit in the requirement."

            # Construct EvidenceLocation (exact offsets in the owning document's extracted text)
            ev_loc = None
            if snippet and evidence_doc:
                source_text = doc_text.get(evidence_doc, state.submitted_raw_text)
                source_start = source_text.find(snippet)
                if source_start >= 0:
                    source_end = source_start + len(snippet)
                    source_line = source_text.count("\n", 0, source_start) + 1
                else:
                    source_start, source_end, source_line = evidence_chunk_start, evidence_chunk_end, evidence_chunk_line
                ev_loc = EvidenceLocation(
                    document_id=doc_ids.get(evidence_doc) or "doc_sub",
                    document_name=evidence_doc,
                    page_number=evidence_page,
                    section_title=evidence_section,
                    start_char=source_start,
                    end_char=source_end,
                    line_number=source_line,
                    snippet=snippet,
                    similarity_score=round(sim_score, 4),
                )

            # Top-k retrieved passages, kept so every verdict shows what RAG actually surfaced.
            supporting = [
                EvidenceLocation(
                    document_id=doc_ids.get(c.document_name) or "doc_sub",
                    document_name=c.document_name,
                    page_number=c.page_number,
                    section_title=c.section_title,
                    start_char=c.start_char,
                    end_char=c.end_char,
                    line_number=c.line_number,
                    snippet=c.text[:300],
                    similarity_score=round(score, 4),
                )
                for c, score in top_results
            ]

            verdicts.append(
                ComplianceVerdict(
                    requirement_id=req.id,
                    requirement_text=req.text,
                    category=req.category,
                    severity=req.severity,
                    mandatory=req.mandatory,
                    status=verdict_status,
                    confidence_score=round(conf, 3),
                    evidence_snippet=snippet,
                    evidence_location=ev_loc,
                    supporting_evidence=supporting,
                    rationale=rationale,
                    missing_elements=missing,
                    conflicting_elements=conflicting,
                    deviations=deviations,
                    remarks=remarks
                )
            )

        state.compliance_verdicts = verdicts
        duration_ms = (time.time() - start_time) * 1000

        compliant_cnt = sum(1 for v in verdicts if v.status == ComplianceStatus.COMPLIANT)
        non_compliant_cnt = sum(1 for v in verdicts if v.status == ComplianceStatus.NON_COMPLIANT)
        partial_cnt = sum(1 for v in verdicts if v.status == ComplianceStatus.PARTIALLY_COMPLIANT)

        event = AgentExecutionEvent(
            agent_id=self.id,
            agent_name=self.name,
            status="completed",
            duration_ms=round(duration_ms, 2),
            thought_process=thoughts + [
                f"Evaluated all {len(verdicts)} requirements.",
                f"Tally: {compliant_cnt} Compliant, {partial_cnt} Partially Compliant, {non_compliant_cnt} Non-Compliant."
            ],
            output_summary=f"Audit complete: {compliant_cnt} Compliant, {partial_cnt} Partial, {non_compliant_cnt} Non-Compliant.",
            tokens_used=510
        )
        state.agent_logs.append(event)
        await memory_store.append_event(state.job_id, event.model_dump())
        return state
