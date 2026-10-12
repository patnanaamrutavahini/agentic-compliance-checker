import React from 'react';
import { ComplianceVerdict } from '../types/compliance';
import { FileX2, GitCompareArrows, Ruler } from 'lucide-react';

interface FindingsPanelProps {
  verdicts: ComplianceVerdict[];
  onSelect: (verdict: ComplianceVerdict) => void;
}

interface ColumnProps {
  title: string;
  icon: React.ReactNode;
  empty: string;
  tone: string;
  rows: { verdict: ComplianceVerdict; items: string[] }[];
  onSelect: (verdict: ComplianceVerdict) => void;
}

const Column: React.FC<ColumnProps> = ({ title, icon, empty, tone, rows, onSelect }) => (
  <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-4">
    <div className={`flex items-center space-x-2 text-xs font-bold uppercase tracking-wider mb-3 ${tone}`}>
      {icon}
      <span>{title} ({rows.length})</span>
    </div>
    {rows.length === 0 ? (
      <p className="text-[11px] text-slate-500 italic">{empty}</p>
    ) : (
      <ul className="space-y-2">
        {rows.map(({ verdict, items }) => (
          <li key={verdict.requirement_id} className="rounded-lg bg-slate-950/60 border border-slate-800 p-2.5 text-[11px]">
            <button onClick={() => onSelect(verdict)} className="font-mono text-brand-400 hover:underline">
              {verdict.requirement_id}
            </button>
            <span className="text-slate-300"> {verdict.requirement_text}</span>
            {items.map((it, i) => (
              <div key={i} className="mt-1 text-slate-400">&rarr; {it}</div>
            ))}
            {verdict.evidence_location && (
              <div className="mt-1 text-[10px] font-mono text-slate-500">
                {verdict.evidence_location.document_name} | p.{verdict.evidence_location.page_number} | line {verdict.evidence_location.line_number}
              </div>
            )}
          </li>
        ))}
      </ul>
    )}
  </div>
);

export const FindingsPanel: React.FC<FindingsPanelProps> = ({ verdicts, onSelect }) => {
  const missing = verdicts
    .filter(v => v.status === 'Non-Compliant' || v.missing_elements.length > 0)
    .map(v => ({ verdict: v, items: v.missing_elements }));
  const conflicting = verdicts
    .filter(v => v.conflicting_elements.length > 0)
    .map(v => ({ verdict: v, items: v.conflicting_elements }));
  const deviating = verdicts
    .filter(v => v.deviations.length > 0)
    .map(v => ({ verdict: v, items: v.deviations }));

  return (
    <div className="glass-panel rounded-2xl p-5 sm:p-6 border border-slate-800/80 mb-8 shadow-xl">
      <h2 className="text-lg font-bold text-white tracking-tight mb-1">Missing, Conflicting & Deviating Information</h2>
      <p className="text-xs text-slate-400 mb-4">
        Each finding links back to its requirement and the document location that supports it. Click an ID to inspect the evidence.
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Column
          title="Missing requirements" tone="text-rose-400" icon={<FileX2 className="w-4 h-4" />}
          empty="No missing requirements detected." rows={missing} onSelect={onSelect}
        />
        <Column
          title="Conflicting information" tone="text-amber-400" icon={<GitCompareArrows className="w-4 h-4" />}
          empty="No conflicts detected." rows={conflicting} onSelect={onSelect}
        />
        <Column
          title="Deviations" tone="text-sky-400" icon={<Ruler className="w-4 h-4" />}
          empty="No deviations detected." rows={deviating} onSelect={onSelect}
        />
      </div>
    </div>
  );
};
