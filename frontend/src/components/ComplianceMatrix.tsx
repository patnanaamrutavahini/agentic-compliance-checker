import React, { useState } from 'react';
import { ComplianceVerdict, ComplianceStatus, SeverityLevel } from '../types/compliance';
import { 
  Search, 
  CheckCircle2, 
  AlertTriangle, 
  AlertOctagon, 
  HelpCircle, 
  ChevronDown, 
  ChevronUp, 
  Edit3, 
  ShieldAlert,
  FileSearch
} from 'lucide-react';

interface ComplianceMatrixProps {
  verdicts: ComplianceVerdict[];
  onSelectEvidence: (verdict: ComplianceVerdict) => void;
  onOpenOverrideModal: (verdict: ComplianceVerdict) => void;
  selectedRequirementId?: string;
}

export const ComplianceMatrix: React.FC<ComplianceMatrixProps> = ({
  verdicts,
  onSelectEvidence,
  onOpenOverrideModal,
  selectedRequirementId
}) => {
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});

  const toggleRow = (id: string) => {
    setExpandedRows(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const filteredVerdicts = verdicts.filter(v => {
    const matchStatus = filterStatus === 'ALL' || v.status === filterStatus;
    const matchSeverity = filterSeverity === 'ALL' || v.severity === filterSeverity;
    const matchSearch = searchQuery === '' || 
      v.requirement_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.requirement_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.category.toLowerCase().includes(searchQuery.toLowerCase());

    return matchStatus && matchSeverity && matchSearch;
  });

  const getStatusBadge = (status: ComplianceStatus) => {
    switch (status) {
      case 'Compliant':
        return {
          bg: 'bg-emerald-950/60 text-emerald-400 border-emerald-500/40',
          icon: CheckCircle2
        };
      case 'Partially Compliant':
        return {
          bg: 'bg-amber-950/60 text-amber-400 border-amber-500/40',
          icon: AlertTriangle
        };
      case 'Non-Compliant':
        return {
          bg: 'bg-rose-950/60 text-rose-400 border-rose-500/40',
          icon: AlertOctagon
        };
      default:
        return {
          bg: 'bg-purple-950/60 text-purple-400 border-purple-500/40',
          icon: HelpCircle
        };
    }
  };

  const getSeverityBadge = (sev: SeverityLevel) => {
    switch (sev) {
      case 'Critical':
        return 'bg-rose-950/80 text-rose-300 border-rose-600/50';
      case 'High':
        return 'bg-amber-950/80 text-amber-300 border-amber-600/50';
      case 'Medium':
        return 'bg-blue-950/80 text-blue-300 border-blue-600/50';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-5 sm:p-6 border border-slate-800/80 mb-8 shadow-xl">
      
      {/* Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-brand-400" />
            Traceable Compliance Matrix
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Every decision is anchored to exact requirement specifications and verified document evidence.
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search clause or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1.5 text-xs bg-slate-900/80 border border-slate-700/80 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500"
            />
          </div>

          {/* Status Filter */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-2.5 py-1.5 text-xs bg-slate-900/80 border border-slate-700/80 rounded-lg text-slate-200 focus:outline-none focus:border-brand-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="Compliant">Compliant</option>
            <option value="Partially Compliant">Partially Compliant</option>
            <option value="Non-Compliant">Non-Compliant</option>
            <option value="Requires Human Review">Requires Human Review</option>
          </select>

          {/* Severity Filter */}
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="px-2.5 py-1.5 text-xs bg-slate-900/80 border border-slate-700/80 rounded-lg text-slate-200 focus:outline-none focus:border-brand-500"
          >
            <option value="ALL">All Severities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
          </select>
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/70">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-900/90 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Req ID</th>
              <th className="py-3 px-4">Category & Severity</th>
              <th className="py-3 px-4">Requirement Statement</th>
              <th className="py-3 px-4">Compliance Status</th>
              <th className="py-3 px-4 text-center">Confidence</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {filteredVerdicts.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500">
                  No matching compliance requirements found.
                </td>
              </tr>
            ) : (
              filteredVerdicts.map((v) => {
                const isExpanded = !!expandedRows[v.requirement_id];
                const isSelected = selectedRequirementId === v.requirement_id;
                const statusBadge = getStatusBadge(v.status);
                const StatusIcon = statusBadge.icon;

                return (
                  <React.Fragment key={v.requirement_id}>
                    <tr className={`transition-colors hover:bg-slate-900/50 ${isSelected ? 'bg-brand-950/30' : ''}`}>
                      
                      {/* ID */}
                      <td className="py-3 px-4 font-mono font-bold text-slate-200">
                        {v.requirement_id}
                      </td>

                      {/* Category & Severity */}
                      <td className="py-3 px-4">
                        <div className="flex flex-col space-y-1">
                          <span className="text-slate-300 font-medium">{v.category}</span>
                          <div className="flex items-center space-x-1.5">
                            <span className={`px-2 py-0.5 rounded text-[9px] font-semibold border ${getSeverityBadge(v.severity)}`}>
                              {v.severity}
                            </span>
                            {v.mandatory && (
                              <span className="text-[9px] text-slate-500 font-mono">Mandatory</span>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Requirement Statement */}
                      <td className="py-3 px-4 max-w-md">
                        <p className="text-slate-200 line-clamp-2 leading-relaxed">
                          {v.requirement_text}
                        </p>
                        {v.human_override?.is_overridden && (
                          <span className="inline-block mt-1 px-1.5 py-0.5 rounded text-[9px] bg-purple-950/80 text-purple-300 border border-purple-800">
                            Human Override Applied
                          </span>
                        )}
                      </td>

                      {/* Status */}
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full border text-[11px] font-semibold ${statusBadge.bg}`}>
                          <StatusIcon className="w-3.5 h-3.5" />
                          <span>{v.status}</span>
                        </span>
                      </td>

                      {/* Confidence */}
                      <td className="py-3 px-4 text-center font-mono font-medium text-slate-300">
                        {Math.round(v.confidence_score * 100)}%
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end space-x-1.5">
                          {/* Inspect Evidence button */}
                          <button
                            onClick={() => onSelectEvidence(v)}
                            title="Inspect Document Evidence"
                            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-brand-900/60 text-slate-300 hover:text-brand-400 border border-slate-700/60 transition"
                          >
                            <FileSearch className="w-3.5 h-3.5" />
                          </button>

                          {/* Override Button */}
                          <button
                            onClick={() => onOpenOverrideModal(v)}
                            title="Human Review Override"
                            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-purple-900/60 text-slate-300 hover:text-purple-300 border border-slate-700/60 transition"
                          >
                            <Edit3 className="w-3.5 h-3.5" />
                          </button>

                          {/* Expand Details */}
                          <button
                            onClick={() => toggleRow(v.requirement_id)}
                            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition"
                          >
                            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                          </button>
                        </div>
                      </td>

                    </tr>

                    {/* Expandable Deep Audit View */}
                    {isExpanded && (
                      <tr className="bg-slate-900/70">
                        <td colSpan={6} className="p-4 border-t border-slate-800/60">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            
                            {/* Left: Auditor Rationale & Remarks */}
                            <div>
                              <span className="text-[10px] font-bold uppercase tracking-wider text-brand-400 block mb-1">
                                Agent Audit Rationale
                              </span>
                              <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                                {v.rationale}
                              </p>

                              {v.remarks && (
                                <div className="mt-2 text-[11px] text-slate-400">
                                  <strong>Remarks:</strong> {v.remarks}
                                </div>
                              )}
                            </div>

                            {/* Right: Evidence Quote & Location */}
                            <div>
                              <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 block mb-1">
                                Ground Truth Evidence Citation
                              </span>
                              {v.evidence_snippet ? (
                                <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800 text-xs">
                                  <blockquote className="italic text-slate-200 border-l-2 border-brand-500 pl-2 mb-2">
                                    "{v.evidence_snippet}"
                                  </blockquote>
                                  {v.evidence_location && (
                                    <div className="text-[10px] font-mono text-slate-400 flex items-center justify-between pt-1 border-t border-slate-800/80">
                                      <span>Doc: {v.evidence_location.document_name}</span>
                                      <span>
                                        Page {v.evidence_location.page_number} ({v.evidence_location.section_title}) | line {v.evidence_location.line_number}
                                        {typeof v.evidence_location.start_char === 'number' ? ` | chars ${v.evidence_location.start_char}-${v.evidence_location.end_char}` : ''}
                                      </span>
                                    </div>
                                  )}
                                </div>
                              ) : (
                                <div className="bg-rose-950/30 p-3 rounded-lg border border-rose-900/40 text-xs text-rose-300">
                                  <strong>Missing Information:</strong> Zero verifiable evidence or statements were detected in the submitted document for this requirement.
                                </div>
                              )}

                              {v.missing_elements && v.missing_elements.length > 0 && (
                                <div className="mt-2 text-[11px] text-rose-400">
                                  <strong>Missing Scope:</strong> {v.missing_elements.join(', ')}
                                </div>
                              )}

                              {v.conflicting_elements && v.conflicting_elements.length > 0 && (
                                <div className="mt-2 text-[11px] text-amber-400">
                                  <strong>Conflicting:</strong> {v.conflicting_elements.join(' | ')}
                                </div>
                              )}

                              {v.deviations && v.deviations.length > 0 && (
                                <div className="mt-2 text-[11px] text-sky-400">
                                  <strong>Deviations:</strong> {v.deviations.join(' | ')}
                                </div>
                              )}
                            </div>

                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
