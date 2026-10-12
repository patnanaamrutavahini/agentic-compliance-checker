import React, { useState } from 'react';
import { ComplianceVerdict, ComplianceStatus } from '../types/compliance';
import { X, Check, UserCheck } from 'lucide-react';

interface HumanReviewModalProps {
  verdict: ComplianceVerdict;
  onClose: () => void;
  onSubmitOverride: (requirementId: string, newStatus: ComplianceStatus, notes: string, reviewerName: string) => void;
}

export const HumanReviewModal: React.FC<HumanReviewModalProps> = ({
  verdict,
  onClose,
  onSubmitOverride
}) => {
  const [selectedStatus, setSelectedStatus] = useState<ComplianceStatus>(verdict.status);
  const [reviewerName, setReviewerName] = useState<string>('Lead Compliance Auditor');
  const [notes, setNotes] = useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!notes.trim()) return;
    onSubmitOverride(verdict.requirement_id, selectedStatus, notes, reviewerName);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="glass-panel w-full max-w-lg rounded-2xl p-6 border border-slate-700/80 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
          <div className="flex items-center space-x-2">
            <UserCheck className="w-5 h-5 text-brand-400" />
            <h3 className="text-base font-bold text-white">
              Human-in-the-Loop Verdict Override
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          
          {/* Target Requirement Info */}
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-mono text-brand-400 font-bold">{verdict.requirement_id}</span>
              <span className="text-slate-400">{verdict.category}</span>
            </div>
            <p className="text-slate-200">{verdict.requirement_text}</p>
            <div className="text-[11px] text-slate-400 pt-1">
              Current Automated Verdict: <strong className="text-amber-400">{verdict.status}</strong>
            </div>
          </div>

          {/* New Status Selection */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Overridden Compliance Status
            </label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value as ComplianceStatus)}
              className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-brand-500"
            >
              <option value="Compliant">Compliant</option>
              <option value="Partially Compliant">Partially Compliant</option>
              <option value="Non-Compliant">Non-Compliant</option>
              <option value="Requires Human Review">Requires Human Review</option>
            </select>
          </div>

          {/* Reviewer Name */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Reviewer Name / Title
            </label>
            <input
              type="text"
              value={reviewerName}
              onChange={(e) => setReviewerName(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-brand-500"
              required
            />
          </div>

          {/* Justification Notes */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Technical Justification & Override Audit Notes
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="State the engineering/regulatory reason for modifying the AI verdict..."
              className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500 resize-none"
              required
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 bg-slate-800/60 hover:bg-slate-800 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-500 rounded-lg shadow-md shadow-brand-500/20 transition flex items-center space-x-1.5"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Apply Override</span>
            </button>
          </div>

        </form>
      </div>
    </div>
  );
};
