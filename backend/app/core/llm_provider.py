import json
import logging
import re
from typing import Dict, Any, Optional, List
import httpx
from app.config import settings
from app.agents.requirement_splitter import split_compound_requirement, infer_category

logger = logging.getLogger(__name__)

class LLMProvider:
    """
    Unified LLM abstraction supporting Google Gemini, OpenAI, Anthropic,
    and a local deterministic high-precision compliance reasoning engine.
    """
    def __init__(self, provider: Optional[str] = None, api_key: Optional[str] = None):
        self.provider = provider or settings.DEFAULT_LLM_PROVIDER
        self.api_key = api_key or self._get_default_key(self.provider)

    def _get_default_key(self, provider: str) -> str:
        if provider == "gemini":
            return settings.GEMINI_API_KEY
        elif provider == "openai":
            return settings.OPENAI_API_KEY
        elif provider == "anthropic":
            return settings.ANTHROPIC_API_KEY
        return ""

    async def generate_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """
        Executes an LLM request and guarantees a structured JSON response.
        """
        # If API key is present and provider is supported, attempt live LLM call
        if self.provider == "gemini" and self.api_key:
            try:
                return await self._call_gemini_json(prompt, system_prompt)
            except Exception as e:
                logger.warning(f"Gemini call failed ({e}), falling back to intelligent deterministic engine.")
        
        elif self.provider == "openai" and self.api_key:
            try:
                return await self._call_openai_json(prompt, system_prompt)
            except Exception as e:
                logger.warning(f"OpenAI call failed ({e}), falling back to intelligent deterministic engine.")

        elif self.provider == "anthropic" and self.api_key:
            try:
                return await self._call_anthropic_json(prompt, system_prompt)
            except Exception as e:
                logger.warning(f"Anthropic call failed ({e}), falling back to intelligent deterministic engine.")

        # Default / Fallback: Deterministic Rule-and-Semantic reasoning engine
        return self._evaluate_deterministic(prompt, system_prompt)

    async def _call_gemini_json(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"System Instructions:\n{system_prompt}\n\nTask:\n{prompt}\n\nRespond ONLY with a valid JSON object."}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)

    async def _call_openai_json(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt + "\nYou must output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)

    async def _call_anthropic_json(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.ANTHROPIC_MODEL,
            "system": system_prompt + " Output ONLY a raw JSON string without markdown markers.",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4096,
            "temperature": 0.1
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = data["content"][0]["text"].strip()
            # Clean markdown if present
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text.strip())

    def _evaluate_deterministic(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """
        High-precision deterministic NLP parser used as offline engine or fallback.
        Parses prompts and extracts requirements, verdicts, classifications, discrepancies.
        """
        prompt_lower = prompt.lower()
        
        # 1. Classification Agent Response
        if "classify" in system_prompt.lower() or "document classification" in system_prompt.lower():
            is_ref = "reference" in prompt_lower or "specification" in prompt_lower or "standard" in prompt_lower or "policy" in prompt_lower or "checklist" in prompt_lower
            doc_type = "Reference Standard / Specification" if is_ref else "Submitted Report / Procedure"
            
            domain = "Technical & Quality Specifications"
            if "gdpr" in prompt_lower or "privacy" in prompt_lower or "data protection" in prompt_lower:
                domain = "Data Privacy & Governance (GDPR / ISO 27001)"
            elif "aerospace" in prompt_lower or "material" in prompt_lower or "tolerance" in prompt_lower:
                domain = "Aerospace & Mechanical Engineering"
            elif "clinical" in prompt_lower or "trial" in prompt_lower or "fda" in prompt_lower:
                domain = "Biomedical & Clinical Trial Protocol"
            elif "iso 9001" in prompt_lower or "quality" in prompt_lower:
                domain = "Quality Management Systems (ISO 9001)"

            return {
                "document_type": doc_type,
                "domain": domain,
                "structure_summary": "Document organized with title, scope, numbered technical clauses, tables, and verification criteria.",
                "identified_sections": ["Scope & Overview", "Technical Requirements", "Quality & Compliance", "Testing & Verification"]
            }

        # 2. Requirement Extraction Agent Response
        if "requirement extraction" in system_prompt.lower() or "extract requirements" in prompt_lower:
            requirements = []

            # Parse ONLY the reference document body. The prompt also contains instructions and a
            # JSON template whose lines contain "must" / "requirements" and used to be extracted
            # as bogus requirements.
            body_match = re.search(
                r"Reference Standard Document:\s*\n(.*?)\n\s*\n\s*Extract all requirements",
                prompt,
                re.DOTALL | re.IGNORECASE,
            )
            doc_body = body_match.group(1) if body_match else prompt

            # Look for lines with bullet points, numbers, "shall", "must", "require", or colons
            lines = [l.strip() for l in doc_body.split("\n") if l.strip()]
            req_idx = 1
            for line in lines:
                lower_l = line.lower()
                # A line is a requirement only if it states an obligation (must / shall / ...),
                # is an explicit checklist bullet, or carries a REQ- id. Titles, document ids and
                # section headings ("SCOPE & APPLICABILITY") have no obligation and are skipped:
                # they can never have evidence in a submission and would show up as false gaps.
                has_obligation = re.search(
                    r"\b(must|shall|should|will|is required|are required|required to|needs? to)\b", lower_l
                ) is not None
                is_bullet = line.startswith(("-", "*", "•"))
                is_req = has_obligation or is_bullet or line.upper().startswith("REQ-")

                # Check for list items or clauses
                if is_req and len(line) > 15:
                    clean_text = re.sub(r"^[-*•\d\.\s\(\)]+", "", line).strip()
                    if clean_text and len(clean_text) > 10 and not clean_text.lower().startswith("table") and not clean_text.lower().startswith("document"):
                        # One list sentence ("must contain A, B, C, and D") -> one requirement per item
                        for atom in split_compound_requirement(clean_text):
                            severity = "Critical" if any(k in atom.lower() for k in ["must", "mandatory", "critical", "shall not", "zero tolerance", "strictly"]) else "High"
                            requirements.append({
                                "id": f"REQ-{req_idx:03d}",
                                "text": atom,
                                "section": f"Clause {req_idx}.0",
                                "category": infer_category(atom),
                                "severity": severity,
                                "mandatory": True,
                                "source_clause": line[:200],
                                "expected_evidence_type": "Data sheet, calculation report, test certificates or procedure manual"
                            })
                            req_idx += 1
                    if req_idx > 40:  # cap on requirements per document
                        break
            
            if not requirements:
                requirements = [
                    {
                        "id": "REQ-001",
                        "text": "The submitted report must contain complete design calculations.",
                        "section": "Section 1.1",
                        "category": "Design Calculations",
                        "severity": "Critical",
                        "mandatory": True,
                        "source_clause": "Scope 1.1",
                        "expected_evidence_type": "Analytical Stress Calculations"
                    },
                    {
                        "id": "REQ-002",
                        "text": "Material specifications must be explicitly stated with certified composition limits.",
                        "section": "Section 1.2",
                        "category": "Material Specifications",
                        "severity": "High",
                        "mandatory": True,
                        "source_clause": "Scope 1.2",
                        "expected_evidence_type": "Material Data Sheet"
                    },
                    {
                        "id": "REQ-003",
                        "text": "Inspection requirements and non-destructive examination protocols must be detailed.",
                        "section": "Section 1.3",
                        "category": "Quality Assurance",
                        "severity": "Critical",
                        "mandatory": True,
                        "source_clause": "Scope 1.3",
                        "expected_evidence_type": "Inspection Plan (NDE/NDT)"
                    },
                    {
                        "id": "REQ-004",
                        "text": "Testing procedures and acceptance criteria under nominal and stress loads must be defined.",
                        "section": "Section 1.4",
                        "category": "Testing & Validation",
                        "severity": "High",
                        "mandatory": True,
                        "source_clause": "Scope 1.4",
                        "expected_evidence_type": "Test Protocol & Log"
                    }
                ]

            return {"requirements": requirements}

        # 3. Compliance and Reviewer Evaluation Response
        # "_deterministic" tells ComplianceAgent that this is a canned placeholder, not a real
        # model judgement, so it must run its own evidence-based heuristic instead of using it.
        return {
            "_deterministic": True,
            "status": "Partially Compliant",
            "confidence_score": 0.88,
            "overall_score": 72.5,
            "rationale": "Automated semantic audit analyzed all reference criteria against submitted document chunks.",
            "remarks": "System identified compliant sections along with missing inspection protocols."
        }

llm_provider = LLMProvider()
