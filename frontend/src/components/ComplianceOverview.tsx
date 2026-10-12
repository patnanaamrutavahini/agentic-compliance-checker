import React from 'react';
import { ComplianceReport, ComplianceStatus } from '../types/compliance';
import { AlertOctagon, CheckCircle2, AlertTriangle, HelpCircle, FileCheck } from 'lucide-react';

interface ComplianceOverviewProps {
  report: ComplianceReport;
}

export const ComplianceOverview: React.FC<ComplianceOverviewProps> = ({ report }) => {
  const getStatusBadge = (status: ComplianceStatus) => {
    switch (status) {
      case 'Compliant':
        return {
          bg: 'bg-emerald-950/60 text-emerald-400 border-emerald-500/30',
          icon: CheckCircle2,
          color: 'text-emerald-400'
        };
      case 'Partially Compliant':
        return {
          bg: 'bg-amber-950/60 text-amber-400 border-amber-500/30',
          icon: AlertTriangle,
          color: 'text-amber-400'
        };
      case 'Non-Compliant':
        return {
          bg: 'bg-rose-950/60 text-rose-400 border-rose-500/30',
          icon: AlertOctagon,
          color: 'text-rose-400'
        };
      default:
        return {
          bg: 'bg-purple-950/60 text-purple-400 border-purple-500/30',
          icon: HelpCircle,
          color: 'text-purple-400'
        };
    }
  };

  const badge = getStatusBadge(report.overall_status);
  const StatusIcon = badge.icon;

  return (
    <div className="glass-panel rounded-2xl p-5 sm:p-6 border border-slate-800/80 mb-8 shadow-xl">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        
        {/* Left Column: Overall Status & Score Gauge */}
        <div className="lg:col-span-4 flex flex-col items-center sm:items-start p-4 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Overall Governance Verdict
          </span>

          <div className={`inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full border text-sm font-bold mb-4 ${badge.bg}`}>
            <StatusIcon className="w-4 h-4" />
            <span>{report.overall_status}</span>
          </div>

          <div className="w-full flex items-baseline justify-between border-t border-slate-800/80 pt-3">
            <div>
              <span className="text-3xl font-extrabold text-white tracking-tight">
                {report.compliance_score}%
              </span>
              <span className="text-xs text-slate-400 ml-2">Compliance Score</span>
            </div>
            <div className="text-right">
              <span className="text-sm font-semibold text-cyan-400">
                {report.confidence_score}%
              </span>
              <p className="text-[10px] text-slate-500">Evidence Confidence</p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-800 rounded-full h-2 mt-3 overflow-hidden">
            <div
              className={`h-full transition-all duration-1000 ${
                report.compliance_score >= 85
                  ? 'bg-emerald-400'
                  : report.compliance_score >= 50
                  ? 'bg-amber-400'
                  : 'bg-rose-500'
              }`}
              style={{ width: `${Math.min(100, Math.max(5, report.compliance_score))}%` }}
            />
          </div>
        </div>

        {/* Right Column: Breakdown Cards */}
        <div className="lg:col-span-8 grid grid-cols-2 sm:grid-cols-4 gap-3">
          
          {/* Card 1: Total Reqs */}
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium">Total Requirements</span>
              <FileCheck className="w-4 h-4 text-cyan-400" />
            </div>
            <span className="text-2xl font-bold text-white">{report.total_requirements}</span>
            <span className="text-[10px] text-slate-500 mt-1">Extracted & Audited</span>
          </div>

          {/* Card 2: Compliant */}
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium">Compliant</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <span className="text-2xl font-bold text-emerald-400">{report.compliant_count}</span>
            <span className="text-[10px] text-slate-500 mt-1">100% Traceable Evidence</span>
          </div>

          {/* Card 3: Partial */}
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium">Partial</span>
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            </div>
            <span className="text-2xl font-bold text-amber-400">{report.partial_count}</span>
            <span className="text-[10px] text-slate-500 mt-1">Incomplete Parameters</span>
          </div>

          {/* Card 4: Non-Compliant / Missing */}
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium">Non-Compliant / Missing</span>
              <AlertOctagon className="w-4 h-4 text-rose-400" />
            </div>
            <span className="text-2xl font-bold text-rose-400">{report.non_compliant_count}</span>
            <span className="text-[10px] text-slate-500 mt-1">{report.critical_violations_count} Critical Violation(s)</span>
          </div>

        </div>

      </div>
    </div>
  );
};
