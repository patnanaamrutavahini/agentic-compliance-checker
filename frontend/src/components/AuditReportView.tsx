import React from 'react';
import { ComplianceReport } from '../types/compliance';
import { Download, FileText, FileSpreadsheet, Code, Sparkles } from 'lucide-react';
import { apiService } from '../services/api';

interface AuditReportViewProps {
  report: ComplianceReport;
}

export const AuditReportView: React.FC<AuditReportViewProps> = ({ report }) => {
  const downloadFile = (content: string, fileName: string, contentType: string) => {
    const a = document.createElement('a');
    const file = new Blob([content], { type: contentType });
    a.href = URL.createObjectURL(file);
    a.download = fileName;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const handleExportCSV = () => {
    let csv = "Req ID,Category,Severity,Status,Confidence,Evidence Snippet,Rationale\n";
    report.requirements_matrix.forEach(v => {
      const snip = (v.evidence_snippet || "NONE").replace(/"/g, '""');
      const rat = v.rationale.replace(/"/g, '""');
      csv += `"${v.requirement_id}","${v.category}","${v.severity}","${v.status}","${Math.round(v.confidence_score * 100)}%","${snip}","${rat}"\n`;
    });
    downloadFile(csv, `compliance_audit_${report.job_id}.csv`, 'text/csv');
  };

  const handleExportJSON = () => {
    const jsonStr = JSON.stringify(report, null, 2);
    downloadFile(jsonStr, `compliance_audit_${report.job_id}.json`, 'application/json');
  };

  const handleExportMarkdown = () => {
    let md = `# Formal Compliance Audit Report\n\n`;
    md += `**Job ID:** \`${report.job_id}\`  \n`;
    md += `**Domain:** ${report.domain}  \n`;
    md += `**Verdict:** ${report.overall_status} (${report.compliance_score}% Compliance Score)  \n\n`;
    md += `## Executive Summary\n${report.executive_summary}\n\n`;
    md += `## Matrix Findings\n`;
    report.requirements_matrix.forEach(v => {
      md += `- **[${v.status}]** \`${v.requirement_id}\` (${v.category}): ${v.requirement_text}\n`;
      if (v.evidence_snippet) md += `  - Evidence: _"${v.evidence_snippet}"_\n`;
      md += `  - Rationale: ${v.rationale}\n\n`;
    });
    downloadFile(md, `compliance_audit_${report.job_id}.md`, 'text/markdown');
  };

  return (
    <div className="glass-panel rounded-2xl p-5 sm:p-6 border border-slate-800/80 mb-8 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80 mb-5">
        <div>
          <div className="flex items-center space-x-2">
            <FileText className="w-5 h-5 text-brand-400" />
            <h2 className="text-lg font-bold text-white tracking-tight">
              Executive Compliance Audit Report & Exports
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Certified multi-agent compliance summary ready for regulatory review, vendor sign-off, or board reporting.
          </p>
        </div>

        {/* Download Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleExportCSV}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-850 text-xs font-medium text-emerald-400 border border-emerald-900/40 transition"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>CSV Matrix</span>
          </button>

          <button
            onClick={handleExportJSON}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-850 text-xs font-medium text-cyan-400 border border-cyan-900/40 transition"
          >
            <Code className="w-3.5 h-3.5" />
            <span>JSON</span>
          </button>

          <button
            onClick={handleExportMarkdown}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-850 text-xs font-medium text-brand-400 border border-brand-900/40 transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Markdown</span>
          </button>

          <a
            href={apiService.exportUrl(report.job_id, 'pdf')}
            download
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-xs font-semibold text-white shadow-md shadow-brand-500/20 transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span>PDF Report</span>
          </a>
        </div>
      </div>

      {/* Executive Summary Memo */}
      <div className="rounded-xl bg-slate-900/70 border border-slate-800 p-5 mb-5">
        <div className="flex items-center space-x-2 text-xs font-bold text-brand-400 uppercase tracking-wider mb-2">
          <Sparkles className="w-4 h-4" />
          <span>Decision & Reviewer Agent Synthesis</span>
        </div>
        <p className="text-sm text-slate-200 leading-relaxed">
          {report.executive_summary}
        </p>
      </div>

      {/* Audit Meta Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
          <span className="text-[10px] text-slate-500 block uppercase font-mono">Job Identifier</span>
          <span className="font-mono text-slate-300">{report.job_id}</span>
        </div>

        <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
          <span className="text-[10px] text-slate-500 block uppercase font-mono">Domain</span>
          <span className="text-slate-300 truncate block">{report.domain}</span>
        </div>

        <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
          <span className="text-[10px] text-slate-500 block uppercase font-mono">Standard Ref</span>
          <span className="text-slate-300 truncate block" title={report.reference_doc_name}>{report.reference_doc_name}</span>
        </div>

        <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
          <span className="text-[10px] text-slate-500 block uppercase font-mono">Audit Timestamp</span>
          <span className="text-slate-300 truncate block">{new Date(report.timestamp).toLocaleString()}</span>
        </div>
      </div>

      {report.pipeline_info && (
        <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
            <span className="text-[10px] text-slate-500 block uppercase font-mono">Workflow Engine</span>
            <span className="text-slate-300">{report.pipeline_info.workflow_engine}</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
            <span className="text-[10px] text-slate-500 block uppercase font-mono">Retrieval (RAG)</span>
            <span className="text-slate-300">{report.pipeline_info.retrieval}</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800">
            <span className="text-[10px] text-slate-500 block uppercase font-mono">Documents Audited</span>
            <span className="text-slate-300">
              {report.pipeline_info.reference_documents} reference / {report.pipeline_info.submitted_documents} submitted
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
