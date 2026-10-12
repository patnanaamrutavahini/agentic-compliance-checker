import React from 'react';
import { SampleScenario } from '../types/compliance';
import { Sparkles, CheckCircle, Plane, Award, ShieldAlert } from 'lucide-react';

interface SampleScenariosProps {
  scenarios: SampleScenario[];
  selectedScenarioId: string;
  onSelectScenario: (scenario: SampleScenario) => void;
  isLoading: boolean;
}

export const SampleScenarios: React.FC<SampleScenariosProps> = ({
  scenarios,
  selectedScenarioId,
  onSelectScenario,
  isLoading
}) => {
  const getIcon = (id: string) => {
    if (id.includes('engineering') || id.includes('aero')) return <Plane className="w-4 h-4 text-cyan-400" />;
    if (id.includes('iso')) return <Award className="w-4 h-4 text-emerald-400" />;
    return <ShieldAlert className="w-4 h-4 text-amber-400" />;
  };

  return (
    <div className="glass-panel rounded-2xl p-4 sm:p-5 border border-slate-800/80 mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-brand-400" />
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
            Pre-Configured Industrial Compliance Benchmarks
          </h2>
        </div>
        <span className="text-xs text-slate-500">Click any scenario for 1-click audit execution</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {scenarios.map((sc) => {
          const isSelected = sc.id === selectedScenarioId;
          return (
            <button
              key={sc.id}
              disabled={isLoading}
              onClick={() => onSelectScenario(sc)}
              className={`text-left p-3.5 rounded-xl border transition-all flex flex-col justify-between ${
                isSelected
                  ? 'bg-brand-950/40 border-brand-500/80 shadow-md shadow-brand-500/10'
                  : 'bg-slate-900/60 border-slate-800/80 hover:bg-slate-850 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center space-x-2">
                    {getIcon(sc.id)}
                    <span className="text-xs font-semibold text-white truncate max-w-[190px]">{sc.title}</span>
                  </div>
                  {isSelected && <CheckCircle className="w-3.5 h-3.5 text-brand-400 flex-shrink-0" />}
                </div>
                <p className="text-[11px] text-slate-400 line-clamp-2 mb-2 leading-relaxed">
                  {sc.description}
                </p>
              </div>
              <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-500">
                <span className="truncate">{sc.domain}</span>
                <span className="text-brand-400 font-medium">Load & Audit &rarr;</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
