import React from 'react';
import { RequirementItem } from '../types/compliance';
import { ListChecks } from 'lucide-react';

interface RequirementsPanelProps {
  requirements: RequirementItem[];
}

const sevClass = (sev: string) =>
  sev === 'Critical' ? 'text-rose-300 border-rose-600/50 bg-rose-950/60'
  : sev === 'High' ? 'text-amber-300 border-amber-600/50 bg-amber-950/60'
  : 'text-blue-300 border-blue-600/50 bg-blue-950/60';

export const RequirementsPanel: React.FC<RequirementsPanelProps> = ({ requirements }) => {
  if (!requirements || requirements.length === 0) return null;
  return (
    <div className="glass-panel rounded-2xl p-5 sm:p-6 border border-slate-800/80 mb-8 shadow-xl">
      <div className="flex items-center space-x-2 mb-1">
        <ListChecks className="w-5 h-5 text-cyan-400" />
        <h2 className="text-lg font-bold text-white tracking-tight">Extracted Requirements</h2>
        <span className="text-xs text-slate-400">({requirements.length})</span>
      </div>
      <p className="text-xs text-slate-400 mb-4">
        Atomic, testable requirements produced by the Requirement Extraction Agent from the reference document(s).
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="text-[10px] uppercase tracking-wider text-slate-500 border-b border-slate-800">
              <th className="py-2 pr-3">ID</th>
              <th className="py-2 pr-3">Requirement</th>
              <th className="py-2 pr-3">Source</th>
              <th className="py-2 pr-3">Category</th>
              <th className="py-2 pr-3">Severity</th>
              <th className="py-2">Mandatory</th>
            </tr>
          </thead>
          <tbody>
            {requirements.map(r => (
              <tr key={r.id} className="border-b border-slate-800/60 align-top">
                <td className="py-2 pr-3 font-mono text-brand-400 whitespace-nowrap">{r.id}</td>
                <td className="py-2 pr-3 text-slate-200">{r.text}</td>
                <td className="py-2 pr-3 text-slate-400 font-mono">
                  {r.source_document ? <div>{r.source_document}</div> : null}
                  <div className="text-slate-500">{r.section}</div>
                </td>
                <td className="py-2 pr-3 text-slate-300">{r.category}</td>
                <td className="py-2 pr-3">
                  <span className={`px-2 py-0.5 rounded border text-[10px] font-semibold ${sevClass(r.severity)}`}>{r.severity}</span>
                </td>
                <td className="py-2 text-slate-300">{r.mandatory ? 'Yes' : 'No'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
