from typing import List, Dict, Any, Optional, Tuple
import re


class DocumentChunk:
    def __init__(self, chunk_id: str, document_name: str, text: str, page_number: int,
                 section_title: str, start_char: int, end_char: int, line_number: int,
                 metadata: Optional[Dict[str, Any]] = None):
        self.chunk_id = chunk_id
        self.document_name = document_name
        self.text = text
        self.page_number = page_number
        self.section_title = section_title
        self.start_char = start_char
        self.end_char = end_char
        self.line_number = line_number
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id, "document_name": self.document_name,
            "text": self.text, "page_number": self.page_number,
            "section_title": self.section_title, "start_char": self.start_char,
            "end_char": self.end_char, "line_number": self.line_number,
            "metadata": self.metadata,
        }


class DocumentChunker:
    """Create retrieval chunks with offsets into the parser's original extracted text.

    PDF page numbers use the parser's page_texts metadata. DOCX/TXT have no reliable
    physical page layout, so page numbers are explicitly marked as approximate.
    """
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = max(1, chunk_size)
        self.chunk_overlap = max(0, min(chunk_overlap, self.chunk_size - 1))

    @staticmethod
    def _page_spans(parsed_doc: Dict[str, Any], raw_text: str) -> List[Tuple[int, int, int]]:
        page_texts = parsed_doc.get("page_texts") or []
        spans: List[Tuple[int, int, int]] = []
        cursor = 0
        for item in page_texts:
            try:
                page_num, page_text = item
            except (TypeError, ValueError):
                continue
            if not page_text:
                continue
            start = raw_text.find(page_text, cursor)
            if start < 0:
                start = raw_text.find(page_text)
            if start < 0:
                continue
            end = start + len(page_text)
            spans.append((int(page_num), start, end))
            cursor = end
        return spans

    @staticmethod
    def _page_for_offset(offset: int, spans: List[Tuple[int, int, int]]) -> int:
        for page_num, start, end in spans:
            if start <= offset < end or (offset == end and start == end):
                return page_num
        return 1

    def chunk_document(self, parsed_doc: Dict[str, Any]) -> List[DocumentChunk]:
        raw_text = parsed_doc.get("raw_text", "") or ""
        doc_name = parsed_doc.get("filename", "unknown_doc")
        page_spans = self._page_spans(parsed_doc, raw_text)
        is_paginated_source = len(page_spans) > 1 or (
            len(page_spans) == 1 and parsed_doc.get("total_pages", 1) == 1
            and str(doc_name).lower().endswith(".pdf")
        )
        sections = parsed_doc.get("sections") or []
        ranges: List[Tuple[str, str, int, int]] = []

        if sections:
            for sec in sections:
                sec_text = sec.get("content", "") or ""
                sec_start = int(sec.get("start_char", 0) or 0)
                title = sec.get("title", "General") or "General"
                # Match paragraph spans so offsets remain anchored to the extracted source.
                matches = list(re.finditer(r"\S.*?(?=\n\s*\n|\Z)", sec_text, flags=re.S))
                pending: List[Tuple[int, int, str]] = []
                pending_len = 0
                for match in matches:
                    para = match.group(0).strip()
                    if not para:
                        continue
                    para_start = match.start() + (len(match.group(0)) - len(match.group(0).lstrip()))
                    para_end = para_start + len(para)
                    if pending and pending_len + len(para) + 2 > self.chunk_size:
                        start = pending[0][0]
                        end = pending[-1][1]
                        ranges.append((title, "\n\n".join(x[2] for x in pending), sec_start + start, sec_start + end))
                        # Keep the previous final paragraph as bounded overlap.
                        overlap_items = pending[-1:] if self.chunk_overlap else []
                        pending = list(overlap_items)
                        pending_len = sum(len(x[2]) for x in pending)
                    pending.append((para_start, para_end, para))
                    pending_len += len(para) + 2
                if pending:
                    ranges.append((title, "\n\n".join(x[2] for x in pending), sec_start + pending[0][0], sec_start + pending[-1][1]))
        elif raw_text:
            step = max(1, self.chunk_size - self.chunk_overlap)
            for start in range(0, len(raw_text), step):
                end = min(len(raw_text), start + self.chunk_size)
                ranges.append(("General", raw_text[start:end], start, end))

        chunks: List[DocumentChunk] = []
        for index, (title, text, start, end) in enumerate(ranges, start=1):
            page = self._page_for_offset(start, page_spans)
            line = raw_text.count("\n", 0, max(0, start)) + 1
            chunks.append(DocumentChunk(
                chunk_id=f"{doc_name}_chk_{index}", document_name=doc_name, text=text,
                page_number=page, section_title=title, start_char=start, end_char=end,
                line_number=line,
                metadata={
                    "section": title,
                    "source_offset_basis": "extracted_text",
                    "page_number_reliable": bool(str(doc_name).lower().endswith(".pdf") and page_spans),
                    "source_start_char": start,
                    "source_end_char": end,
                },
            ))
        return chunks
