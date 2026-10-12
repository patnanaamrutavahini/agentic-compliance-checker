import React from 'react';
import { ShieldCheck, Cpu, Key, BookOpen } from 'lucide-react';

interface HeaderProps {
  onOpenApiKeyModal: () => void;
  activeProvider: string;
}

export const Header: React.FC<HeaderProps> = ({ onOpenApiKeyModal, activeProvider }) => {
  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-slate-800/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand & Logo */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-cyan-400 p-0.5 flex items-center justify-center shadow-lg shadow-brand-500/20">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-brand-400 animate-pulse-slow" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="font-bold text-lg text-white tracking-tight">Antigravity</h1>
              <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider bg-brand-500/10 text-brand-400 border border-brand-500/20 rounded-full">
                Compliance AI
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Multi-Agent Document Intelligence & Evidence Traceability
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-3">
          {/* Active Model Indicator */}
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
            <Cpu className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-slate-400">Agent Engine:</span>
            <span className="font-medium text-slate-200 capitalize">{activeProvider || 'Deterministic RAG'}</span>
          </div>

          {/* Configure LLM API Key */}
          <button
            onClick={onOpenApiKeyModal}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700/80 transition shadow-sm hover:border-brand-500/50"
          >
            <Key className="w-3.5 h-3.5 text-amber-400" />
            <span>API Keys</span>
          </button>

          {/* Quick Docs Link */}
          <a
            href="#architecture-section"
            className="hidden md:flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs text-slate-300 border border-slate-800 transition"
          >
            <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
            <span>Agent Architecture</span>
          </a>
        </div>
      </div>
    </header>
  );
};
