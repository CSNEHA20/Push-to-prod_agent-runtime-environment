import React from 'react';
import { ShieldCheck, Award, Zap, Cpu, RefreshCw } from 'lucide-react';

export default function ARCScoreCard({ scoreData }) {
  if (!scoreData) {
    scoreData = {
      overall: 84.5,
      rating_label: "High Reliability (A-Tier)",
      metrics: {
        reliability: 92.0,
        context_quality: 78.5,
        reasoning_depth: 88.0,
        efficiency: 71.0,
        recovery: 91.0
      }
    };
  }

  const { overall, rating_label, metrics } = scoreData;

  const getScoreColor = (val) => {
    if (val >= 90) return 'text-emerald-400 bg-emerald-500/20 border-emerald-500/30';
    if (val >= 80) return 'text-cyan-400 bg-cyan-500/20 border-cyan-500/30';
    if (val >= 70) return 'text-amber-400 bg-amber-500/20 border-amber-500/30';
    return 'text-rose-400 bg-rose-500/20 border-rose-500/30';
  };

  const getBarColor = (val) => {
    if (val >= 90) return 'bg-gradient-to-r from-emerald-500 to-teal-400';
    if (val >= 80) return 'bg-gradient-to-r from-cyan-500 to-blue-400';
    if (val >= 70) return 'bg-gradient-to-r from-amber-500 to-yellow-400';
    return 'bg-gradient-to-r from-rose-500 to-red-400';
  };

  const items = [
    { label: 'Reliability', value: metrics.reliability, icon: ShieldCheck },
    { label: 'Context Quality', value: metrics.context_quality, icon: Cpu },
    { label: 'Reasoning Depth', value: metrics.reasoning_depth, icon: Award },
    { label: 'Efficiency', value: metrics.efficiency, icon: Zap },
    { label: 'Recovery Score', value: metrics.recovery, icon: RefreshCw }
  ];

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-2xl backdrop-blur-md">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800/80 pb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">ARC Quality Rating</h3>
          <p className="text-xs text-slate-500">Composite multi-engine performance metric</p>
        </div>
        <div className={`px-3 py-1 rounded-full border text-xs font-bold ${getScoreColor(overall)}`}>
          {rating_label}
        </div>
      </div>

      <div className="flex items-center gap-6 mb-5">
        <div className="flex flex-col items-center justify-center bg-slate-950/80 border border-slate-800 rounded-2xl w-24 h-24 shadow-inner">
          <span className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
            {overall}
          </span>
          <span className="text-[10px] uppercase tracking-widest text-slate-500 mt-1">/ 100</span>
        </div>

        <div className="flex-1 space-y-2.5">
          {items.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <span className="flex items-center gap-1.5 text-slate-300 font-medium">
                    <Icon className="w-3.5 h-3.5 text-cyan-400" />
                    {item.label}
                  </span>
                  <span className="font-mono text-slate-400 font-bold">{item.value}%</span>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-700 ease-out ${getBarColor(item.value)}`}
                    style={{ width: `${item.value}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
