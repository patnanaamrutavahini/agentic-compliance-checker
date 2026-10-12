import React, { useEffect, useMemo, useRef, useState } from 'react';
import { ComplianceVerdict, DocItem, RequirementItem } from '../types/compliance';
import { FileSearch, Sparkles, MapPin, AlertOctagon } from 'lucide-react';

interface EvidenceViewerProps {
  selectedVerdict?: ComplianceVerdict;
  requirement?: RequirementItem;
  referenceDocs: DocItem[];
  submittedDocs: DocItem[];
}

type Span = [number, number];

/** Locate `needle` in `text` (exact, then case-insensitive, then a leading fragment). */
function findSpan(text: string, needle?: string): Span | null {
  if (!needle) return null;
  const hay = text.toLowerCase();
  for (const probe of [needle, needle.slice(0, 60)]) {
    const p = probe.trim().toLowerCase();
    if (p.length < 8) continue;
    const idx = hay.indexOf(p);
    if (idx >= 0) return [idx, idx + p.length];
  }
  return null;
}

const Highlighted: React.FC<{ text: string; span: Span | null; tone: 'cyan' | 'emerald' | 'rose' }> = ({ text, span, tone }) => {
  const markRef = useRef<HTMLElement>(null);
  useEffect(() => {
    markRef.current?.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }, [span?.[0], span?.[1], text]);

  const toneClass = {
    cyan: 'bg-cyan-950/80 text-cyan-200 border-cyan-700/60',
    emerald: 'bg-emerald-950/80 text-emerald-200 border-emerald-700/60',
    rose: 'bg-rose-950/80 text-rose-200 border-rose-700/60',
  }[tone];

  if (!span) return <>{text}</>;
  return (
    <>
      {text.slice(0, span[0])}
      <mark ref={markRef} className={`${toneClass} border rounded px-0.5 font-semibold`}>
        {text.slice(span[0], span[1])}
      </mark>
      {text.slice(span[1])}
    </>
  );
};

export const EvidenceViewer: React.FC<EvidenceViewerProps> = ({
  selectedVerdict,
  requirement,
  referenceDocs,
  submittedDocs,
}) => {
  const location = selectedVerdict?.evidence_location;
  const snippet = selectedVerdict?.evidence_snippet;

  const [activeSubName, setActiveSubName] = useState<string>('');
  const [activeRefName, setActiveRefName] = useState<string>('');

  // Jump to the document that actually holds the evidence / the requirement.
  useEffect(() => {
    if (location?.document_name) setActiveSubName(location.document_name);
    else if (submittedDocs[0]) setActiveSubName(submittedDocs[0].name);
  }, [selectedVerdict?.requirement_id, location?.document_name, submittedDocs.length]);

  useEffect(() => {
    if (requirement?.source_document) setActiveRefName(requirement.source_document);
    else if (referenceDocs[0]) setActiveRefName(referenceDocs[0].name);
  }, [selectedVerdict?.requirement_id, requirement?.source_document, referenceDocs.length]);

  const subDoc = submittedDocs.find(d => d.name === activeSubName) || submittedDocs[0];
  const refDoc = referenceDocs.find(d => d.name === activeRefName) || referenceDocs[0];

  const subSpan = useMemo<Span | null>(() => {
    if (!subDoc || !snippet || !location || location.document_name !== subDoc.name) return null;
    const { start_char: s, end_char: e } = location;
    if (typeof s === 'number' && typeof e === 'number' && subDoc.text.slice(s, e) === snippet) return [s, e];
    return findSpan(subDoc.text, snippet);
  }, [subDoc, snippet, location]);

  const refSpan = useMemo<Span | null>(() => {
    if (!refDoc || !selectedVerdict) return null;
    return findSpan(refDoc.text, requirement?.source_clause) || findSpan(refDoc.text, selectedVerdict.requirement_text);
  }, [refDoc, requirement, selectedVerdict]);

  if (!selectedVerdict) {
    return (
      <div className="glass-panel rounded-2xl p-6 border border-slate-800/80 mb-8 text-center text-slate-500">
        <FileSearch className="w-8 h-8 mx-auto mb-2 text-slate-600" />
        <p className="text-sm font-medium">Select a requirement from the Compliance Matrix above to inspect side-by-side evidence.</p>
      </div>
    );
  }

  const isOmission = selectedVerdict.status === 'Non-Compliant' && !!snippet;
  const supporting = selectedVerdict.supporting_evidence || [];

  const DocTabs: React.FC<{ docs: DocItem[]; active?: DocItem; onPick: (n: string) => void }> = ({ docs, active, onPick }) =>
    docs.length > 1 ? (
      <div className="flex flex-wrap gap-1 mb-2">
        {docs.map(d => (
          <button
            key={d.name}
            onClick={() => onPick(d.name)}
            className={`px-2 py-0.5 rounded text-[10px] font-mono border transition ${
              active?.name === d.name
                ? 'bg-brand-900/70 border-brand-600/70 text-brand-200'
                : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
          >
            {d.name}
          </button>
        ))}
      </div>
    ) : null;

  return (
    <div className="glass-panel rounded-2xl p-5 sm:p-6 border border-slate-800/80 mb-8 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800/80 mb-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-mono text-xs px-2 py-0.5 rounded bg-brand-500/20 text-brand-400 border border-brand-500/30">
              {selectedVerdict.requirement_id}
            </span>
            <h2 className="text-base font-bold text-white tracking-tight">Dual Document Evidence Inspector</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Auditing: <span className="text-slate-200 font-medium">{selectedVerdict.requirement_text}</span>
          </p>
        </div>

        {location && (
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
            <MapPin className="w-3.5 h-3.5 text-brand-400" />
            <span className="font-mono">{location.document_name}</span>
            <span className="text-slate-500">&bull;</span>
            <span>Page {location.page_number} ({location.section_title})</span>
            <span className="text-slate-500">&bull;</span>
            <span>Line {location.line_number}</span>
            {typeof location.start_char === 'number' && (
              <>
                <span className="text-slate-500">&bull;</span>
                <span className="font-mono">chars {location.start_char}-{location.end_char}</span>
              </>
            )}
            <span className="text-slate-500">&bull;</span>
            <span className="text-cyan-400 font-mono">Match: {Math.round((location.similarity_score ?? 0) * 100)}%</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Reference pane */}
        <div className="flex flex-col rounded-xl bg-slate-900/80 border border-slate-800 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider">1. Reference Requirement</span>
            <span className="text-[10px] text-slate-500 font-mono">{refDoc?.name}</span>
          </div>
          <DocTabs docs={referenceDocs} active={refDoc} onPick={setActiveRefName} />
          <div className="h-64 overflow-y-auto rounded-lg bg-slate-950/80 p-3 text-xs font-mono text-slate-300 leading-relaxed border border-slate-800/60 whitespace-pre-wrap">
            {refDoc ? <Highlighted text={refDoc.text} span={refSpan} tone="cyan" /> : null}
          </div>
        </div>

        {/* Submitted pane */}
        <div className="flex flex-col rounded-xl bg-slate-900/80 border border-slate-800 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-brand-400 uppercase tracking-wider">2. Submitted Document Evidence</span>
            <span className="text-[10px] text-slate-500 font-mono">{subDoc?.name}</span>
          </div>
          <DocTabs docs={submittedDocs} active={subDoc} onPick={setActiveSubName} />
          <div className="h-64 overflow-y-auto rounded-lg bg-slate-950/80 p-3 text-xs font-mono text-slate-300 leading-relaxed border border-slate-800/60 whitespace-pre-wrap">
            {snippet && subDoc ? (
              <Highlighted text={subDoc.text} span={subSpan} tone={isOmission ? 'rose' : 'emerald'} />
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center text-rose-400 p-4">
                <AlertOctagon className="w-8 h-8 mb-2 opacity-80" />
                <p className="font-semibold text-xs">No Document Evidence Found</p>
                <p className="text-[11px] text-slate-400 mt-1 max-w-xs">
                  The requirement was not evidenced in the submitted documents. It is never assumed compliant.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Retrieved passages (RAG trace) */}
      {supporting.length > 0 && (
        <div className="mt-4">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-2">
            Retrieved passages (top {supporting.length}, ranked by hybrid semantic + lexical score)
          </span>
          <div className="space-y-1.5">
            {supporting.map((ev, i) => (
              <div key={i} className="rounded-lg bg-slate-950/60 border border-slate-800 px-3 py-2 text-[11px]">
                <div className="flex flex-wrap items-center gap-x-2 text-slate-400 font-mono">
                  <span>#{i + 1}</span>
                  <span>{ev.document_name}</span>
                  <span>p.{ev.page_number}</span>
                  <span>{ev.section_title}</span>
                  <span>line {ev.line_number}</span>
                  <span className="text-cyan-400">score {Math.round((ev.similarity_score ?? 0) * 100)}%</span>
                </div>
                <p className="text-slate-300 mt-1 line-clamp-2">{ev.snippet}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-brand-400 flex-shrink-0" />
          <span className="text-slate-300">
            <strong>Verdict Rationale:</strong> {selectedVerdict.rationale}
          </span>
        </div>
        <span className="font-mono text-[11px] text-slate-400 flex-shrink-0">
          Confidence: <strong>{Math.round(selectedVerdict.confidence_score * 100)}%</strong>
        </span>
      </div>
    </div>
  );
};
