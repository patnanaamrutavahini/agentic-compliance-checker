import React, { useRef, useState } from 'react';
import { ArrowRight, UploadCloud, Layers, ShieldCheck, RefreshCw, FileText, X, Plus } from 'lucide-react';
import { apiService } from '../services/api';
import { DocItem } from '../types/compliance';

interface DocumentUploadProps {
  referenceDocs: DocItem[];
  setReferenceDocs: (docs: DocItem[]) => void;
  submittedDocs: DocItem[];
  setSubmittedDocs: (docs: DocItem[]) => void;
  onRunAudit: () => void;
  onLoadMultiDocDemo?: () => void;
  isLoading: boolean;
}

interface DocPaneProps {
  role: 'reference' | 'submitted';
  title: string;
  dot: string;
  docs: DocItem[];
  setDocs: (docs: DocItem[]) => void;
  onError: (msg: string) => void;
}

const DocPane: React.FC<DocPaneProps> = ({ role, title, dot, docs, setDocs, onError }) => {
  const fileInput = useRef<HTMLInputElement>(null);
  const [pasted, setPasted] = useState<string>('');
  const [busy, setBusy] = useState<boolean>(false);

  const handleFiles = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    e.target.value = '';
    if (files.length === 0) return;
    setBusy(true);
    onError('');
    const added: DocItem[] = [];
    for (const file of files) {
      try {
        added.push(await apiService.uploadFile(file, role));
      } catch (err: any) {
        const detail = err?.response?.data?.detail;
        onError(typeof detail === 'string' ? detail : `Could not parse ${file.name}. Check that the backend is running and the file is a valid PDF, DOCX, or TXT document.`);
      }
    }
    if (added.length > 0) setDocs([...docs, ...added]);
    setBusy(false);
  };

  const addPasted = () => {
    if (!pasted.trim()) return;
    const n = docs.filter(d => d.name.startsWith(`pasted_${role}`)).length + 1;
    setDocs([...docs, { name: `pasted_${role}_${n}.txt`, text: pasted }]);
    setPasted('');
  };

  const removeDoc = (index: number) => setDocs(docs.filter((_, i) => i !== index));

  return (
    <div className="flex flex-col rounded-xl bg-slate-900/80 border border-slate-800 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className={`w-2.5 h-2.5 rounded-full ${dot}`}></span>
          <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">{title}</span>
        </div>

        <input
          type="file"
          ref={fileInput}
          onChange={handleFiles}
          accept=".pdf,.docx,.doc,.txt,.md"
          multiple
          className="hidden"
        />
        <button
          onClick={() => fileInput.current?.click()}
          disabled={busy}
          className="flex items-center space-x-1 px-2.5 py-1 text-[11px] font-medium text-brand-400 bg-brand-950/60 hover:bg-brand-900/60 border border-brand-800/60 rounded-md transition disabled:opacity-50"
        >
          {busy ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <UploadCloud className="w-3.5 h-3.5" />}
          <span>{busy ? 'Parsing...' : 'Upload PDF/DOCX/TXT (multiple)'}</span>
        </button>
      </div>

      {/* Ingested documents */}
      <div className="space-y-2 mb-3 max-h-48 overflow-y-auto">
        {docs.length === 0 && (
          <p className="text-[11px] text-slate-500 italic">No documents yet. Upload one or more files, or paste text below.</p>
        )}
        {docs.map((d, i) => (
          <div key={`${d.name}-${i}`} className="flex items-start justify-between rounded-lg bg-slate-950/70 border border-slate-800 px-3 py-2">
            <div className="min-w-0">
              <div className="flex items-center space-x-1.5 text-xs text-slate-200">
                <FileText className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                <span className="truncate font-mono">{d.name}</span>
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">
                {d.text.length.toLocaleString()} chars{d.pages ? ` | ${d.pages} page(s)` : ''}
              </div>
              <div className="text-[10px] text-slate-600 mt-0.5 truncate max-w-[28rem]">{d.text.slice(0, 120).replace(/\s+/g, ' ')}</div>
            </div>
            <button
              onClick={() => removeDoc(i)}
              aria-label={`Remove ${d.name}`}
              className="p-1 text-slate-500 hover:text-rose-400 transition flex-shrink-0"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>

      {/* Paste text */}
      <textarea
        value={pasted}
        onChange={(e) => setPasted(e.target.value)}
        placeholder={role === 'reference'
          ? 'Paste reference standard requirements, clauses, or checklist text...'
          : 'Paste submitted report, procedure, or lab log text...'}
        rows={3}
        className="w-full text-xs font-mono bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-brand-500/80 focus:ring-1 focus:ring-brand-500/50 resize-y leading-relaxed"
      />
      <button
        onClick={addPasted}
        disabled={!pasted.trim()}
        className="mt-2 self-start flex items-center space-x-1 px-2.5 py-1 text-[11px] font-medium text-slate-300 bg-slate-800/80 hover:bg-slate-700 border border-slate-700 rounded-md transition disabled:opacity-40"
      >
        <Plus className="w-3.5 h-3.5" />
        <span>Add pasted text as a document</span>
      </button>
    </div>
  );
};

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  referenceDocs,
  setReferenceDocs,
  submittedDocs,
  setSubmittedDocs,
  onRunAudit,
  onLoadMultiDocDemo,
  isLoading
}) => {
  const [uploadError, setUploadError] = useState<string>('');

  return (
    <div className="glass-panel rounded-2xl p-5 sm:p-6 border border-slate-800/80 mb-8 shadow-xl">
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 mb-5">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
            <Layers className="w-5 h-5 text-brand-400" />
            Multi-Document Ingestion & Agent Audit Runner
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Add one or more Reference Specifications / checklists and one or more Submitted documents. Supports PDF, DOCX, and TXT.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row w-full lg:w-auto gap-2">
          {onLoadMultiDocDemo && (
            <button
              onClick={onLoadMultiDocDemo}
              disabled={isLoading}
              className="px-4 py-3 rounded-xl bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-200 font-medium text-xs transition disabled:opacity-50"
            >
              Load multi-document demo
            </button>
          )}
          <button
            onClick={onRunAudit}
            disabled={isLoading || referenceDocs.length === 0 || submittedDocs.length === 0}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-brand-600 via-sky-500 to-cyan-500 hover:from-brand-500 hover:to-cyan-400 text-white font-semibold text-sm shadow-lg shadow-brand-500/25 transition-all flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Agents Auditing Documents...</span>
              </>
            ) : (
              <>
                <ShieldCheck className="w-4 h-4" />
                <span>Run Multi-Agent Compliance Audit</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>

      {uploadError && (
        <div role="alert" className="mb-4 rounded-lg border border-rose-700/70 bg-rose-950/40 p-3 text-sm text-rose-200">
          {uploadError}
          <button type="button" className="ml-3 underline underline-offset-2" onClick={() => setUploadError('')}>Dismiss</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DocPane
          role="reference"
          title="1. Reference Standards / Specifications"
          dot="bg-cyan-400"
          docs={referenceDocs}
          setDocs={setReferenceDocs}
          onError={setUploadError}
        />
        <DocPane
          role="submitted"
          title="2. Submitted Documents / Reports"
          dot="bg-brand-400"
          docs={submittedDocs}
          setDocs={setSubmittedDocs}
          onError={setUploadError}
        />
      </div>
    </div>
  );
};
