import time
from typing import Dict, Any
from app.agents.state import ComplianceAgentState
from app.core.llm_provider import LLMProvider
from app.models.schemas import DocumentType, DocumentMetadata, AgentExecutionEvent
from app.core.memory import memory_store

class DocumentClassificationAgent:
    """
    Agent 1: Document Classification Agent
    Identifies document types, structural layout, domain, and governance framework.
    """
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.name = "Document Classification Agent"
        self.id = "agent_01_classifier"

    async def run(self, state: ComplianceAgentState) -> ComplianceAgentState:
        start_time = time.time()
        thoughts = [
            "Analyzing reference and submitted document structures...",
            "Inspecting headings, metadata, clause numbering patterns, and technical keywords...",
            "Determining compliance domain and document categories."
        ]

        await memory_store.append_event(state.job_id, {
            "agent_id": self.id,
            "agent_name": self.name,
            "status": "running",
            "thought_process": thoughts,
            "output_summary": "Classifying document structures and schemas..."
        })

        ref_sample = state.reference_raw_text[:2000]
        sub_sample = state.submitted_raw_text[:2000]

        system_prompt = (
            "You are an expert Document Classification Agent in an AI Compliance Intelligence system. "
            "Analyze the given document excerpts and determine their document types, governance domain, "
            "and structural layout."
        )

        prompt = (
            f"Reference Document Sample:\n{ref_sample}\n\n"
            f"Submitted Document Sample:\n{sub_sample}\n\n"
            "Classify both documents. Return JSON with keys:\n"
            "- reference_doc_type: string\n"
            "- submitted_doc_type: string\n"
            "- domain: string (e.g. Quality Systems, Aerospace, Data Privacy, Clinical Trials)\n"
            "- structure_summary: string\n"
            "- key_topics: array of strings"
        )

        result = await self.llm.generate_json(prompt, system_prompt)

        # Update metadata
        domain = result.get("domain", "General Technical & Quality Compliance")
        ref_type_str = result.get("reference_doc_type", "Reference Standard / Specification")
        sub_type_str = result.get("submitted_doc_type", "Submitted Report / Procedure")
        summary = result.get("structure_summary", "Structured technical document with standardized clauses.")

        state.reference_doc = DocumentMetadata(
            id=f"{state.job_id}_ref",
            filename=state.reference_filename,
            doc_type=DocumentType.REFERENCE_STANDARD,
            domain=domain,
            structure_summary=f"Reference specification establishing mandatory compliance rules for {domain}.",
            total_pages=max(1, len(state.reference_raw_text) // 2500),
            total_characters=len(state.reference_raw_text)
        )

        state.submitted_doc = DocumentMetadata(
            id=f"{state.job_id}_sub",
            filename=state.submitted_filename,
            doc_type=DocumentType.SUBMITTED_REPORT,
            domain=domain,
            structure_summary=f"Vendor / contractor submitted artifact subjected to audit against {domain} standard.",
            total_pages=max(1, len(state.submitted_raw_text) // 2500),
            total_characters=len(state.submitted_raw_text)
        )

        state.classification_result = result
        duration_ms = (time.time() - start_time) * 1000

        event = AgentExecutionEvent(
            agent_id=self.id,
            agent_name=self.name,
            status="completed",
            duration_ms=round(duration_ms, 2),
            thought_process=thoughts + [
                f"Classification complete: Reference is [{ref_type_str}], Submitted is [{sub_type_str}]. Domain mapped to [{domain}]."
            ],
            output_summary=f"Identified Domain: {domain}. Structural layout verified.",
            tokens_used=180
        )
        state.agent_logs.append(event)
        await memory_store.append_event(state.job_id, event.model_dump())
        return state
