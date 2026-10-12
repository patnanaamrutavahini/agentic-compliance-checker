import io
import csv
import json
from typing import Dict, Any
from app.models.schemas import ComplianceReport

class ExportService:
    @staticmethod
    def generate_csv(report: ComplianceReport) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header Metadata
        writer.writerow(["AGENTIC AI COMPLIANCE AUDIT REPORT"])
        writer.writerow(["Job ID", report.job_id])
        writer.writerow(["Timestamp", report.timestamp.isoformat()])
        writer.writerow(["Domain", report.domain])
        writer.writerow(["Reference Document", report.reference_doc_name])
        writer.writerow(["Submitted Document", report.submitted_doc_name])
        writer.writerow(["Overall Verdict", report.overall_status.value])
        writer.writerow(["Compliance Score", f"{report.compliance_score}%"])
        writer.writerow([])
        
        # Matrix Table
        writer.writerow([
            "Req ID",
            "Category",
            "Severity",
            "Mandatory",
            "Requirement Statement",
            "Status",
            "Confidence",
            "Evidence Snippet",
            "Evidence Document",
            "Page",
            "Section",
            "Line",
            "Char Range",
            "Missing",
            "Conflicting",
            "Deviations",
            "Remarks",
            "Rationale"
        ])

        for v in report.requirements_matrix:
            loc = v.evidence_location
            writer.writerow([
                v.requirement_id,
                v.category,
                v.severity.value,
                "YES" if v.mandatory else "NO",
                v.requirement_text,
                v.status.value,
                f"{round(v.confidence_score * 100, 1)}%",
                v.evidence_snippet or "NONE",
                loc.document_name if loc else "N/A",
                loc.page_number if loc else "",
                loc.section_title if loc else "",
                loc.line_number if loc else "",
                f"{loc.start_char}-{loc.end_char}" if loc and loc.start_char is not None else "",
                " | ".join(v.missing_elements),
                " | ".join(v.conflicting_elements),
                " | ".join(v.deviations),
                v.remarks,
                v.rationale
            ])

        return output.getvalue()

    @staticmethod
    def generate_markdown(report: ComplianceReport) -> str:
        md = []
        md.append(f"# Compliance Audit Report: {report.submitted_doc_name}\n")
        md.append(f"**Job ID:** `{report.job_id}`  ")
        md.append(f"**Domain:** {report.domain}  ")
        md.append(f"**Reference Standard(s):** {report.reference_doc_name}  ")
        md.append(f"**Submitted Document(s):** {report.submitted_doc_name}  ")
        md.append(f"**Overall Compliance Verdict:** **{report.overall_status.value}** ({report.compliance_score}% Compliance Score)  \n")
        
        md.append("## Executive Summary\n")
        md.append(f"{report.executive_summary}\n\n")

        md.append("## Compliance Summary Metrics\n")
        md.append(f"- **Total Requirements Audited:** {report.total_requirements}")
        md.append(f"- **Compliant:** {report.compliant_count}")
        md.append(f"- **Partially Compliant:** {report.partial_count}")
        md.append(f"- **Non-Compliant / Missing:** {report.non_compliant_count}")
        md.append(f"- **Critical Violations:** {report.critical_violations_count}\n\n")

        md.append("## Requirements Compliance Matrix\n")
        md.append("| Req ID | Category | Severity | Verdict | Confidence | Evidence & Citation | Rationale |")
        md.append("|---|---|---|---|---|---|---|")
        for v in report.requirements_matrix:
            el = v.evidence_location
            loc = f"{el.document_name}, p.{el.page_number}, line {el.line_number}" if el else "Missing"
            ev = f"\"{v.evidence_snippet[:80]}...\" ({loc})" if v.evidence_snippet else "_No evidence found_"
            md.append(f"| `{v.requirement_id}` | {v.category} | {v.severity.value} | **{v.status.value}** | {round(v.confidence_score * 100, 1)}% | {ev} | {v.rationale} |")

        findings = [(v, "Missing", v.missing_elements) for v in report.requirements_matrix if v.missing_elements]
        findings += [(v, "Conflicting", v.conflicting_elements) for v in report.requirements_matrix if v.conflicting_elements]
        findings += [(v, "Deviation", v.deviations) for v in report.requirements_matrix if v.deviations]
        if findings:
            md.append("\n## Missing, Conflicting & Deviating Information\n")
            for v, kind, items in findings:
                md.append(f"- **{kind}** `{v.requirement_id}`: " + "; ".join(items))

        if report.discrepancies:
            md.append("\n## Discrepancies, Gaps & Remediation Actions\n")
            for d in report.discrepancies:
                md.append(f"### Gap {d.id}: {d.discrepancy_type} ({d.severity.value})")
                md.append(f"- **Expected Requirement:** {d.expected_statement}")
                md.append(f"- **Found Statement:** {d.found_statement or 'None'}")
                md.append(f"- **Remediation Recommendation:** {d.remediation_recommendation}\n")

        return "\n".join(md)

    @staticmethod
    def generate_json_str(report: ComplianceReport) -> str:
        return json.dumps(report.model_dump(mode="json"), indent=2, default=str)

    @staticmethod
    def generate_pdf(report: ComplianceReport) -> bytes:
        from xml.sax.saxutils import escape
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        styles = getSampleStyleSheet()
        small = styles["BodyText"].clone("small")
        small.fontSize = 7.5
        small.leading = 9.5

        def p(text, style=small):
            return Paragraph(escape(str(text if text is not None else "")), style)

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=12 * mm, rightMargin=12 * mm,
                                topMargin=12 * mm, bottomMargin=12 * mm, title=f"Compliance Audit {report.job_id}")
        story = [
            Paragraph("Compliance Audit Report", styles["Title"]),
            p(f"Job {report.job_id} | Domain: {report.domain}", styles["BodyText"]),
            p(f"Reference: {report.reference_doc_name}", styles["BodyText"]),
            p(f"Submitted: {report.submitted_doc_name}", styles["BodyText"]),
            Spacer(1, 4 * mm),
            Paragraph(f"Compliance Status: <b>{escape(report.overall_status.value)}</b> "
                      f"({report.compliance_score}% weighted score)", styles["Heading2"]),
            p(f"Requirements: {report.total_requirements} | Compliant: {report.compliant_count} | "
              f"Partial: {report.partial_count} | Non-compliant: {report.non_compliant_count} | "
              f"Human review: {report.human_review_count}", styles["BodyText"]),
            Spacer(1, 3 * mm),
            Paragraph("Executive Summary", styles["Heading3"]),
            p(report.executive_summary, styles["BodyText"]),
            Spacer(1, 4 * mm),
            Paragraph("Requirements Compliance Matrix", styles["Heading3"]),
        ]
        rows = [[p(h) for h in ("ID", "Requirement", "Status", "Evidence (verbatim)", "Location", "Findings")]]
        for v in report.requirements_matrix:
            loc = v.evidence_location
            where = (f"{loc.document_name}; p.{loc.page_number}; {loc.section_title}; line {loc.line_number}; "
                     f"chars {loc.start_char}-{loc.end_char}") if loc else "No evidence located"
            findings = []
            if v.missing_elements:
                findings.append("Missing: " + "; ".join(v.missing_elements))
            if v.conflicting_elements:
                findings.append("Conflicting: " + "; ".join(v.conflicting_elements))
            if v.deviations:
                findings.append("Deviations: " + "; ".join(v.deviations))
            if v.remarks:
                findings.append("Remarks: " + v.remarks)
            rows.append([p(v.requirement_id), p(v.requirement_text), p(v.status.value),
                         p(v.evidence_snippet or "NONE"), p(where), p(" ".join(findings))])
        table = Table(rows, colWidths=[18 * mm, 62 * mm, 26 * mm, 62 * mm, 45 * mm, 52 * mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#94a3b8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(table)
        if report.discrepancies:
            story += [Spacer(1, 4 * mm), Paragraph("Discrepancies & Remediation", styles["Heading3"])]
            for d in report.discrepancies:
                story.append(p(f"{d.id} [{d.severity.value}] {d.discrepancy_type} ({d.requirement_id}): "
                               f"{d.description} Remediation: {d.remediation_recommendation}", styles["BodyText"]))
        doc.build(story)
        return buf.getvalue()
