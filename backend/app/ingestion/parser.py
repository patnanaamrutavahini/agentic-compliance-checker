import os
import io
import re
from typing import Dict, Any, List, Optional
import docx
import pypdf

class DocumentParser:
    """
    Multi-format parser for PDF, DOCX, and TXT files.
    Preserves page boundaries, headings, tabular content, and structural hierarchy.
    """

    @staticmethod
    def parse_file(file_path: str, filename: str) -> Dict[str, Any]:
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            return DocumentParser._parse_pdf(file_path, filename)
        elif ext in [".docx", ".doc"]:
            return DocumentParser._parse_docx(file_path, filename)
        else:
            return DocumentParser._parse_txt(file_path, filename)

    @staticmethod
    def parse_raw_text(text: str, filename: str = "raw_input.txt") -> Dict[str, Any]:
        return DocumentParser._process_text_structure(text, filename, total_pages=1, page_texts=[(1, text)])

    @staticmethod
    def _parse_pdf(file_path: str, filename: str) -> Dict[str, Any]:
        full_text_pages = []
        try:
            reader = pypdf.PdfReader(file_path)
            total_pages = len(reader.pages)
            for page_idx, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                full_text_pages.append((page_idx, page_text))
        except Exception as e:
            # Fallback if binary parsing fails
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return DocumentParser.parse_raw_text(content, filename)

        combined_text = "\n\n--- Page Break ---\n\n".join([t[1] for t in full_text_pages])
        return DocumentParser._process_text_structure(combined_text, filename, total_pages=len(full_text_pages), page_texts=full_text_pages)

    @staticmethod
    def _parse_docx(file_path: str, filename: str) -> Dict[str, Any]:
        try:
            doc = docx.Document(file_path)
            paragraphs = []
            sections = []
            current_section = "Introduction"

            for p in doc.paragraphs:
                text = p.text.strip()
                if not text:
                    continue
                if p.style.name.startswith("Heading") or re.match(r"^(\d+(\.\d+)*|[A-Z]\.)\s+", text):
                    current_section = text
                paragraphs.append(text)

            # Extract tables
            table_texts = []
            for table in doc.tables:
                table_rows = []
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells]
                    table_rows.append(" | ".join(row_cells))
                if table_rows:
                    table_texts.append("\n[TABLE]\n" + "\n".join(table_rows) + "\n[/TABLE]")

            full_text = "\n\n".join(paragraphs + table_texts)
            return DocumentParser._process_text_structure(full_text, filename, total_pages=1, page_texts=[(1, full_text)])
        except Exception:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return DocumentParser.parse_raw_text(content, filename)

    @staticmethod
    def _parse_txt(file_path: str, filename: str) -> Dict[str, Any]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return DocumentParser.parse_raw_text(content, filename)

    @staticmethod
    def _process_text_structure(
        raw_text: str, 
        filename: str, 
        total_pages: int = 1,
        page_texts: Optional[List[tuple]] = None
    ) -> Dict[str, Any]:
        # Extract sections using regex for headings
        lines = raw_text.split("\n")
        sections = []
        current_title = "Overview & Scope"
        current_content = []
        start_char = 0
        current_char = 0

        section_pattern = re.compile(r"^(section\s+\d+|clause\s+\d+|\d+\.\d+|\d+\.0|[A-Z\s]{4,}:|[IVXLCDM]+\.)\s*(.*)", re.IGNORECASE)

        for line in lines:
            stripped = line.strip()
            if section_pattern.match(stripped) and len(stripped) < 100:
                if current_content:
                    sec_text = "\n".join(current_content).strip()
                    nonempty_preamble = [item.strip() for item in current_content if item.strip()]
                    # A lone document title (for example, "SPECIFICATION AERO-101")
                    # is metadata, not a section. Avoid creating a fake "Overview & Scope"
                    # section before the first real heading. Preserve meaningful preambles.
                    preamble_is_document_title = (
                        not sections
                        and len(nonempty_preamble) == 1
                        and (
                            nonempty_preamble[0].isupper()
                            or re.match(
                                r"^(specification|standard|policy|procedure|technical report)\b",
                                nonempty_preamble[0],
                                re.IGNORECASE,
                            ) is not None
                        )
                    )
                    if sec_text and not preamble_is_document_title:
                        sections.append({
                            "title": current_title,
                            "content": sec_text,
                            "start_char": start_char,
                            "end_char": current_char,
                            "length": len(sec_text)
                        })
                    current_content = []
                    start_char = current_char
                current_title = stripped
            current_content.append(line)
            current_char += len(line) + 1

        if current_content:
            sec_text = "\n".join(current_content)
            sections.append({
                "title": current_title,
                "content": sec_text,
                "start_char": start_char,
                "end_char": current_char,
                "length": len(sec_text)
            })

        # Count tables
        tables_found = len(re.findall(r"(\|[^\n]+\||\bTABLE\b)", raw_text, re.IGNORECASE))

        return {
            "filename": filename,
            "total_pages": total_pages,
            "total_characters": len(raw_text),
            "total_sections": len(sections),
            "raw_text": raw_text,
            "sections": sections,
            "tables_found": tables_found,
            "page_texts": page_texts or [(1, raw_text)]
        }
