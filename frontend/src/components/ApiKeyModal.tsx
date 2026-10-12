import React, { useState } from 'react';
import { X, Key, Check, ShieldCheck } from 'lucide-react';

interface ApiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeProvider: string;
  onSaveConfig: (provider: string, apiKey: string) => void;
}

export const ApiKeyModal: React.FC<ApiKeyModalProps> = ({
  isOpen,
  onClose,
  activeProvider,
  onSaveConfig
}) => {
  const [provider, setProvider] = useState<string>(activeProvider || 'gemini');
  const [apiKey, setApiKey] = useState<string>(() => localStorage.getItem('agentic_llm_api_key') || '');

  if (!isOpen) return null;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('agentic_llm_provider', provider);
    localStorage.setItem('agentic_llm_api_key', apiKey);
    onSaveConfig(provider, apiKey);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="glass-panel w-full max-w-md rounded-2xl p-6 border border-slate-700/80 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
          <div className="flex items-center space-x-2">
            <Key className="w-5 h-5 text-amber-400" />
            <h3 className="text-base font-bold text-white">
              LLM Agent Engine Settings
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          
          {/* Provider Selection */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Select LLM Provider
            </label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-brand-500"
            >
              <option value="gemini">Google Gemini (Gemini 1.5/2.0 Flash/Pro)</option>
              <option value="openai">OpenAI (GPT-4o, GPT-4o-mini)</option>
              <option value="anthropic">Anthropic (Claude 3.5 Sonnet)</option>
              <option value="mock">Local Deterministic Engine (Offline / Zero-Key)</option>
            </select>
          </div>

          {/* API Key Input */}
          {provider !== 'mock' && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                {provider.toUpperCase()} API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-... or AIza..."
                className="w-full px-3 py-2 text-xs font-mono bg-slate-900 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-600 focus:outline-none focus:border-brand-500"
              />
              <p className="text-[10px] text-slate-500 mt-1">
                Keys are stored only in your local session and sent securely to backend endpoints.
              </p>
            </div>
          )}

          {provider === 'mock' && (
            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400 leading-relaxed">
              <strong className="text-slate-200 block mb-1 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                Zero-Config Local Engine Active
              </strong>
              Uses embedded semantic vector similarity, BM25 indexing, and strict regex clause parsing without requiring any external API keys or network credits.
            </div>
          )}

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
              <span>Save Configuration</span>
            </button>
          </div>

        </form>
      </div>
    </div>
  );
};
