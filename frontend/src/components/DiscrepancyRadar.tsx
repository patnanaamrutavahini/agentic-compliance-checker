import React from 'react';
import { DiscrepancyItem, SeverityLevel } from '../types/compliance';
import { AlertTriangle, CheckCircle, Wrench } from 'lucide-react';

interface DiscrepancyRadarProps {
  discrepancies: DiscrepancyItem[];
}

export const DiscrepancyRadar: React.FC<DiscrepancyRadarProps> = ({ discrepancies }) => {
  if (!discrepancies || discrepancies.length === 0) {
    return (
      <div className="glass-panel rounded-2xl p-6 border border-slate-800/80 mb-8 flex items-center justify-center space-x-3 text-emerald-400">
        <CheckCircle className="w-5 h-5" />
        <span className="text-sm font-semibold">Zero Discrepancies Detected. Document is 100% compliant with all standard criteria.</span>
      </div>
    );
  }

  const getSeverityBadge = (sev: SeverityLevel) => {
    switch (sev) {
      case 'Critical':
        return 'bg-rose-950/80 text-rose-300 border-rose-600/50';
      case 'High':
        return 'bg-amber-950/80 text-amber-300 border-amber-600/50';
      default:
        return 'bg-blue-950/80 text-blue-300 border-blue-600/50';
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-5 sm:p-6 border border-slate-800/80 mb-8 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            Compliance Gaps & Discrepancy Analysis
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Agent 5 (Discrepancy Agent) identified {discrepancies.length} discrepancy item(s) requiring remediation.
          </p>
        </div>
        <span className="px-3 py-1 rounded-full bg-rose-950/80 text-rose-300 border border-rose-700/60 text-xs font-semibold">
          {discrepancies.filter(d => d.severity === 'Critical').length} Critical Risk(s)
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {discrepancies.map((disc) => (
          <div
            key={disc.id}
            className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between hover:border-slate-700 transition"
          >
            <div>
              {/* Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-xs font-bold text-slate-300">{disc.id}</span>
                  <span className="text-[10px] text-slate-500 font-mono">({disc.requirement_id})</span>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getSeverityBadge(disc.severity)}`}>
                  {disc.severity} Risk
                </span>
              </div>

              <h3 className="text-xs font-bold text-slate-100 mb-1">
                {disc.discrepancy_type}
              </h3>
              <p className="text-xs text-slate-300 mb-3 leading-relaxed">
                {disc.description}
              </p>

              {/* Comparison Box */}
              <div className="space-y-2 text-[11px] mb-3">
                <div className="p-2 rounded bg-slate-950/80 border border-slate-800">
                  <span className="text-slate-500 block text-[9px] uppercase font-bold">Standard Requirement:</span>
                  <span className="text-slate-200">{disc.expected_statement}</span>
                </div>
                <div className="p-2 rounded bg-slate-950/80 border border-slate-800">
                  <span className="text-slate-500 block text-[9px] uppercase font-bold">Submitted Document Statement:</span>
                  <span className="text-amber-300 italic">{disc.found_statement || 'Missing in Document'}</span>
                </div>
              </div>
            </div>

            {/* Remediation Footer */}
            <div className="pt-3 border-t border-slate-800/80 flex items-start space-x-2 text-xs">
              <Wrench className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
              <div className="text-[11px]">
                <strong className="text-cyan-300">Remediation Action: </strong>
                <span className="text-slate-300">{disc.remediation_recommendation}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
