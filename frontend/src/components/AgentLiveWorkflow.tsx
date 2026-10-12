import React, { useState } from 'react';
import { AgentExecutionEvent } from '../types/compliance';
import { 
  FileSearch, 
  Binary, 
  ListOrdered, 
  ShieldCheck, 
  AlertTriangle, 
  Award, 
  CheckCircle2, 
  Clock, 
  Cpu, 
  Sparkles
} from 'lucide-react';

interface AgentLiveWorkflowProps {
  agentLogs: AgentExecutionEvent[];
  isLoading: boolean;
}

const AGENT_CONFIGS = [
  {
    id: "agent_01_classifier",
    name: "Document Classification Agent",
    role: "Type & Structure Identification",
    icon: FileSearch,
    color: "from-blue-500 to-indigo-600",
    border: "border-blue-500/40"
  },
  {
    id: "agent_02_extractor",
    name: "Information Extraction Agent",
    role: "Sections, Tables & Values",
    icon: Binary,
    color: "from-indigo-500 to-violet-600",
    border: "border-indigo-500/40"
  },
  {
    id: "agent_03_req_extractor",
    name: "Requirement Extraction Agent",
    role: "Atomic Requirement Decomposer",
    icon: ListOrdered,
    color: "from-cyan-500 to-teal-600",
    border: "border-cyan-500/40"
  },
  {
    id: "agent_04_compliance",
    name: "Compliance Agent",
    role: "RAG Semantic Grounding",
    icon: ShieldCheck,
    color: "from-sky-500 to-blue-600",
    border: "border-sky-500/40"
  },
  {
    id: "agent_05_discrepancy",
    name: "Discrepancy Agent",
    role: "Gaps, Contradictions & Deviations",
    icon: AlertTriangle,
    color: "from-amber-500 to-orange-600",
    border: "border-amber-500/40"
  },
  {
    id: "agent_06_reviewer",
    name: "Decision / Reviewer Agent",
    role: "Anti-Hallucination Audit & Report",
    icon: Award,
    color: "from-emerald-500 to-teal-600",
    border: "border-emerald-500/40"
  }
];

export const AgentLiveWorkflow: React.FC<AgentLiveWorkflowProps> = ({ agentLogs, isLoading }) => {
  const [selectedAgentId, setSelectedAgentId] = useState<string>("agent_04_compliance");

  const getAgentEvent = (agentId: string) => {
    return agentLogs.find(e => e.agent_id === agentId);
  };

  const selectedLog = agentLogs.find(e => e.agent_id === selectedAgentId) || agentLogs[0];

  return (
    <div id="architecture-section" className="glass-panel rounded-2xl p-5 sm:p-6 border border-slate-800/80 mb-8 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <div className="flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-brand-400" />
            <h2 className="text-lg font-bold text-white tracking-tight">
              Agentic Multi-Agent Orchestration Graph
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            6 Specialized Autonomous Agents collaborating through shared memory, RAG embeddings, and anti-hallucination guardrails.
          </p>
        </div>

        {/* Live Status Pill */}
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs text-slate-300">
          <span className={`w-2 h-2 rounded-full ${isLoading ? 'bg-amber-400 animate-ping' : 'bg-emerald-400'}`}></span>
          <span>{isLoading ? 'Pipeline In Execution' : 'Workflow Verified'}</span>
        </div>
      </div>

      {/* Interactive 6-Agent Node Pipeline */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        {AGENT_CONFIGS.map((cfg, idx) => {
          const event = getAgentEvent(cfg.id);
          const isSelected = selectedAgentId === cfg.id;
          const isCompleted = event?.status === 'completed';
          const isRunning = isLoading && !isCompleted;
          const Icon = cfg.icon;

          return (
            <button
              key={cfg.id}
              onClick={() => setSelectedAgentId(cfg.id)}
              className={`relative text-left p-3.5 rounded-xl border transition-all flex flex-col justify-between ${
                isSelected
                  ? `bg-slate-900/90 ${cfg.border} shadow-lg shadow-brand-500/10 ring-1 ring-brand-500/50`
                  : 'bg-slate-950/60 border-slate-800/80 hover:bg-slate-900/60 hover:border-slate-700'
              }`}
            >
              <div>
                {/* Node Step Badge */}
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                    0{idx + 1}
                  </span>
                  {isCompleted ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : isRunning ? (
                    <Clock className="w-4 h-4 text-amber-400 animate-spin" />
                  ) : (
                    <span className="w-2 h-2 rounded-full bg-slate-700"></span>
                  )}
                </div>

                {/* Icon & Title */}
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 flex items-center justify-center mb-2">
                  <Icon className="w-4 h-4 text-slate-200" />
                </div>
                <h3 className="text-xs font-bold text-white line-clamp-2 mb-1">
                  {cfg.name}
                </h3>
                <p className="text-[10px] text-slate-400 line-clamp-1">
                  {cfg.role}
                </p>
              </div>

              {event?.duration_ms && (
                <div className="mt-3 pt-2 border-t border-slate-800/60 text-[10px] text-slate-400 flex items-center justify-between">
                  <span>Latency</span>
                  <span className="font-mono text-cyan-400">{event.duration_ms}ms</span>
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Selected Agent Deep Dive & Thought Log Stream */}
      {selectedLog && (
        <div className="rounded-xl bg-slate-950/80 border border-slate-800/80 p-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800/60 mb-3">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-brand-400" />
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                {selectedLog.agent_name} &bull; Internal Thought Stream & Execution Telemetry
              </span>
            </div>
            <div className="flex items-center space-x-3 text-[11px] text-slate-400 font-mono">
              <span>Tokens: <strong className="text-slate-200">{selectedLog.tokens_used || 240}</strong></span>
              <span>&bull;</span>
              <span>Status: <strong className="text-emerald-400 uppercase">{selectedLog.status}</strong></span>
            </div>
          </div>

          <div className="space-y-2 font-mono text-xs">
            {selectedLog.thought_process?.map((t, idx) => (
              <div key={idx} className="flex items-start space-x-2 text-slate-300">
                <span className="text-brand-500 select-none">&rsaquo;</span>
                <span className="leading-relaxed">{t}</span>
              </div>
            ))}
            {selectedLog.output_summary && (
              <div className="mt-3 p-2.5 rounded-lg bg-brand-950/30 border border-brand-800/40 text-brand-300 flex items-start space-x-2">
                <span className="font-bold uppercase text-[10px] tracking-wider text-brand-400">Output:</span>
                <span>{selectedLog.output_summary}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
