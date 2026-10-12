import time
import re
from typing import List, Dict, Any
from app.agents.state import ComplianceAgentState
from app.core.llm_provider import LLMProvider
from app.models.schemas import RequirementItem, SeverityLevel, AgentExecutionEvent
from app.core.memory import memory_store
from app.agents.requirement_splitter import split_compound_requirement, infer_category

class RequirementExtractionAgent:
    """
    Agent 3: Requirement Extraction Agent
    Converts reference standards, policies, and specifications into atomic,
    verifiable, structured requirements with strict severity and category classifications.
    """
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.name = "Requirement Extraction Agent"
        self.id = "agent_03_req_extractor"

    async def run(self, state: ComplianceAgentState) -> ComplianceAgentState:
        start_time = time.time()
        thoughts = [
            "Scanning reference document for normative keywords: 'must', 'shall', 'required', 'mandatory', 'contain'...",
            "Decomposing compound sentences into atomic, testable requirements...",
            "Assigning category tags, severity ratings (Critical, High, Medium), and expected evidence types."
        ]

        await memory_store.append_event(state.job_id, {
            "agent_id": self.id,
            "agent_name": self.name,
            "status": "running",
            "thought_process": thoughts,
            "output_summary": "Extracting atomic requirements from reference standard..."
        })

        ref_text = state.reference_raw_text
        
        system_prompt = (
            "You are an expert Requirement Extraction Agent. Convert the reference document into a list of "
            "atomic, verifiable compliance requirements. Each requirement must be unambiguous and independently checkable. "
            "Do not merge multiple distinct requirements into one."
        )

        prompt = (
            f"Reference Standard Document:\n{ref_text}\n\n"
            "Extract all requirements in JSON with format:\n"
            "{\n"
            '  "requirements": [\n'
            '    {\n'
            '      "id": "REQ-001",\n'
            '      "text": "The submitted report must contain complete design calculations.",\n'
            '      "section": "Section 1.0",\n'
            '      "category": "Design Calculations",\n'
            '      "severity": "Critical",\n'
            '      "mandatory": true,\n'
            '      "source_clause": "The submitted report must contain...",\n'
            '      "expected_evidence_type": "Analytical calculations, FEA reports, or formulas"\n'
            '    }\n'
            '  ]\n'
            "}"
        )

        result = await self.llm.generate_json(prompt, system_prompt)
        raw_reqs = result.get("requirements", [])
        
        parsed_requirements: List[RequirementItem] = []
        split_happened = False
        for idx, r in enumerate(raw_reqs, start=1):
            req_id = r.get("id") or f"REQ-{idx:03d}"
            text = r.get("text", "").strip()
            if not text:
                continue

            sev_str = r.get("severity", "High").capitalize()
            severity = SeverityLevel.HIGH
            if "Crit" in sev_str:
                severity = SeverityLevel.CRITICAL
            elif "Med" in sev_str:
                severity = SeverityLevel.MEDIUM
            elif "Low" in sev_str:
                severity = SeverityLevel.LOW
            elif "Info" in sev_str:
                severity = SeverityLevel.INFO

            # Atomic requirements: a list sentence ("must contain A, B, C, and D") becomes one
            # requirement per item. source_clause keeps the original sentence for traceability.
            parts = split_compound_requirement(text)
            was_split = len(parts) > 1
            split_happened = split_happened or was_split
            for part in parts:
                parsed_requirements.append(RequirementItem(
                    id=req_id,
                    text=part,
                    section=r.get("section", f"Clause {idx}"),
                    category=infer_category(part) if was_split else r.get("category", "General Requirement"),
                    severity=severity,
                    mandatory=r.get("mandatory", True),
                    source_clause=r.get("source_clause", text[:100]) if not was_split else text,
                    expected_evidence_type=r.get("expected_evidence_type", "Textual / Tabular Verification")
                ))

        if split_happened:  # keep ids unique and sequential after splitting
            for n, item in enumerate(parsed_requirements, start=1):
                item.id = f"REQ-{n:03d}"

        # Fallback if list is empty
        if not parsed_requirements:
            # Generate atomic requirements directly from sentences with 'must' or 'contain'
            sentences = re.split(r"[.\n]", ref_text)
            req_c = 1
            for s in sentences:
                s_clean = s.strip()
                if len(s_clean) > 15 and any(w in s_clean.lower() for w in ["must", "shall", "required", "contain", "specif", "test"]):
                    for atom in split_compound_requirement(s_clean):
                        parsed_requirements.append(
                            RequirementItem(
                                id=f"REQ-{req_c:03d}",
                                text=atom,
                                section=f"Section {req_c}.0",
                                category=infer_category(atom),
                                severity=SeverityLevel.HIGH,
                                mandatory=True,
                                source_clause=s_clean,
                                expected_evidence_type="Document Proof"
                            )
                        )
                        req_c += 1

        state.requirements = parsed_requirements
        duration_ms = (time.time() - start_time) * 1000

        event = AgentExecutionEvent(
            agent_id=self.id,
            agent_name=self.name,
            status="completed",
            duration_ms=round(duration_ms, 2),
            thought_process=thoughts + [
                f"Generated {len(parsed_requirements)} structured atomic requirements.",
                f"Requirements categorised across: {list(set([r.category for r in parsed_requirements]))}."
            ],
            output_summary=f"Extracted and categorized {len(parsed_requirements)} atomic requirements.",
            tokens_used=320
        )
        state.agent_logs.append(event)
        await memory_store.append_event(state.job_id, event.model_dump())
        return state
