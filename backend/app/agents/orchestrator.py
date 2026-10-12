import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict

from app.agents.state import ComplianceAgentState
from app.agents.classification_agent import DocumentClassificationAgent
from app.agents.info_extraction_agent import InformationExtractionAgent
from app.agents.req_extraction_agent import RequirementExtractionAgent
from app.agents.compliance_agent import ComplianceAgent
from app.agents.discrepancy_agent import DiscrepancyAgent
from app.agents.reviewer_agent import DecisionReviewerAgent
from app.core.llm_provider import LLMProvider
from app.ingestion.parser import DocumentParser
from app.ingestion.chunker import DocumentChunker
from app.ingestion.vector_store import HybridVectorStore
from app.models.schemas import ComplianceReport, ComplianceStatus, SeverityLevel
from app.core.memory import memory_store

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    """LangGraph channel: the shared blackboard travels as a single value."""
    state: ComplianceAgentState


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().casefold()


class MultiAgentComplianceOrchestrator:
    """Runs the 6-agent workflow as a LangGraph StateGraph.

    classification -> information extraction -> requirement extraction
        -> compliance (RAG) -> discrepancy -> decision/reviewer

    If `langgraph` is not installed the same agents run through a plain sequential
    loop; the engine actually used is recorded in `report.pipeline_info`.
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm = llm_provider or LLMProvider()
        self.chunker = DocumentChunker(chunk_size=400, chunk_overlap=80)

    # ------------------------------------------------------------------ graph
    def _build_graph(self, agents: List[Any]):
        from langgraph.graph import StateGraph, END

        def make_node(agent):
            async def node(gs: GraphState) -> Dict[str, Any]:
                st = gs["state"]
                st.current_agent = agent.name
                return {"state": await agent.run(st)}
            return node

        graph = StateGraph(GraphState)
        for agent in agents:
            graph.add_node(agent.id, make_node(agent))
        graph.set_entry_point(agents[0].id)
        for left, right in zip(agents, agents[1:]):
            graph.add_edge(left.id, right.id)
        graph.add_edge(agents[-1].id, END)
        return graph.compile()

    async def _run_agents(self, agents: List[Any], state: ComplianceAgentState):
        try:
            graph = self._build_graph(agents)
        except ImportError:
            logger.warning("langgraph not installed; running agents sequentially.")
            for agent in agents:
                state.current_agent = agent.name
                state = await agent.run(state)
            return state, "sequential (langgraph not installed)"
        result = await graph.ainvoke({"state": state})
        return result["state"], "langgraph"

    # ----------------------------------------------------------------- ingest
    def _ingest(self, docs: List[Dict[str, Any]], prefix: str) -> List[Dict[str, Any]]:
        """Normalise input docs -> [{document_id, filename, text, parsed}]."""
        out = []
        seen: Dict[str, int] = {}
        for idx, d in enumerate(docs, start=1):
            name = d.get("filename") or d.get("name") or f"{prefix}_{idx}.txt"
            # Evidence is keyed by filename, so keep names unique within one side.
            if name in seen:
                seen[name] += 1
                stem, dot, ext = name.rpartition(".")
                name = f"{stem}_{seen[name]}.{ext}" if dot else f"{name}_{seen[name]}"
            else:
                seen[name] = 1
            text = d.get("text") or ""
            out.append({
                "document_id": d.get("document_id") or f"{prefix}_{idx}",
                "filename": name,
                "text": text,
                "parsed": d.get("parsed") or DocumentParser.parse_raw_text(text, name),
            })
        return out

    @staticmethod
    def _combine(docs: List[Dict[str, Any]]) -> str:
        if len(docs) == 1:
            return docs[0]["text"]
        return "\n\n".join(d["text"] for d in docs)

    # --------------------------------------------------------------- workflow
    async def execute_compliance_workflow(
        self,
        job_id: str,
        reference_text: Optional[str] = None,
        submitted_text: Optional[str] = None,
        reference_filename: str = "Reference_Standard.txt",
        submitted_filename: str = "Submitted_Report.txt",
        domain: str = "General Compliance",
        reference_documents: Optional[List[Dict[str, Any]]] = None,
        submitted_documents: Optional[List[Dict[str, Any]]] = None,
    ) -> ComplianceReport:
        logger.info("Starting multi-agent compliance workflow job_id=%s", job_id)

        if not reference_documents:
            reference_documents = [{"filename": reference_filename, "text": reference_text or ""}]
        if not submitted_documents:
            submitted_documents = [{"filename": submitted_filename, "text": submitted_text or ""}]

        ref_docs = self._ingest(reference_documents, "ref")
        sub_docs = self._ingest(submitted_documents, "sub")
        ref_names = [d["filename"] for d in ref_docs]
        sub_names = [d["filename"] for d in sub_docs]

        # Step 0: chunk every submitted document and index it in a per-job vector store.
        store = HybridVectorStore(name=f"job_{job_id}")
        all_chunks = []
        for d in sub_docs:
            for chunk in self.chunker.chunk_document(d["parsed"]):
                chunk.metadata["document_id"] = d["document_id"]
                all_chunks.append(chunk)
        try:
            await asyncio.to_thread(store.add_chunks, all_chunks)

            state = ComplianceAgentState(
                job_id=job_id,
                reference_raw_text=self._combine(ref_docs),
                submitted_raw_text=self._combine(sub_docs),
                reference_filename=", ".join(ref_names),
                submitted_filename=", ".join(sub_names),
                reference_documents=[{k: d[k] for k in ("document_id", "filename", "text")} for d in ref_docs],
                submitted_documents=[{k: d[k] for k in ("document_id", "filename", "text")} for d in sub_docs],
                submitted_chunks=[c.to_dict() for c in all_chunks],
            )

            agents = [
                DocumentClassificationAgent(self.llm),
                InformationExtractionAgent(self.llm),
                RequirementExtractionAgent(self.llm),
                ComplianceAgent(self.llm, store),
                DiscrepancyAgent(self.llm),
                DecisionReviewerAgent(self.llm),
            ]
            state, engine = await self._run_agents(agents, state)
            retrieval_mode = store.retrieval_mode
        finally:
            store.close()

        self._attribute_requirements(state, ref_docs)

        counts = {s: sum(1 for v in state.compliance_verdicts if v.status == s) for s in ComplianceStatus}
        crit_violations = sum(
            1 for v in state.compliance_verdicts
            if v.severity == SeverityLevel.CRITICAL and v.status == ComplianceStatus.NON_COMPLIANT
        )

        report = ComplianceReport(
            job_id=state.job_id,
            timestamp=datetime.now(timezone.utc),
            reference_doc_name=state.reference_filename,
            submitted_doc_name=state.submitted_filename,
            reference_doc_names=ref_names,
            submitted_doc_names=sub_names,
            domain=state.reference_doc.domain if state.reference_doc else domain,
            overall_status=state.overall_status,
            compliance_score=state.compliance_score,
            confidence_score=state.confidence_score,
            total_requirements=len(state.compliance_verdicts),
            compliant_count=counts[ComplianceStatus.COMPLIANT],
            partial_count=counts[ComplianceStatus.PARTIALLY_COMPLIANT],
            non_compliant_count=counts[ComplianceStatus.NON_COMPLIANT],
            human_review_count=counts[ComplianceStatus.REQUIRES_HUMAN_REVIEW],
            critical_violations_count=crit_violations,
            executive_summary=state.executive_summary,
            requirements=state.requirements,
            requirements_matrix=state.compliance_verdicts,
            discrepancies=state.discrepancies,
            agent_audit_trail=state.agent_logs,
            classification=state.classification_result,
            pipeline_info={
                "workflow_engine": engine,
                "retrieval": retrieval_mode,
                "llm_provider": self.llm.provider,
                "reference_documents": str(len(ref_docs)),
                "submitted_documents": str(len(sub_docs)),
            },
            export_formats={
                "json": f"/api/export/{state.job_id}/json",
                "csv": f"/api/export/{state.job_id}/csv",
                "markdown": f"/api/export/{state.job_id}/markdown",
                "pdf": f"/api/export/{state.job_id}/pdf",
            },
        )
        await memory_store.save_state(f"report_{state.job_id}", report.model_dump(mode="json"))
        return report

    @staticmethod
    def _attribute_requirements(state: ComplianceAgentState, ref_docs: List[Dict[str, Any]]) -> None:
        """Record which reference document each requirement came from."""
        normalized = [(d["filename"], _normalize(d["text"])) for d in ref_docs]
        for req in state.requirements:
            probe = _normalize(req.source_clause or req.text)[:80]
            full = _normalize(req.text)
            owner = None
            for name, text in normalized:
                if (probe and probe in text) or (full and full in text):
                    owner = name
                    break
            req.source_document = owner or (normalized[0][0] if len(normalized) == 1 else None)
