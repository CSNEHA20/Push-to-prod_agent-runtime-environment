import React from 'react';
import { AlertTriangle, ShieldAlert, CheckCircle2, BookmarkPlus } from 'lucide-react';

export default function ARCPredictBanner({ prediction }) {
  if (!prediction) {
    prediction = {
      will_fail: true,
      risk_percent: 73.0,
      reason: "Confidence trend declining & context quality score dropped below 0.65.",
      preemptive_checkpoint: true
    };
  }

  const { will_fail, risk_percent, reason, preemptive_checkpoint } = prediction;

  if (!will_fail && risk_percent < 40) {
    return (
      <div className="bg-emerald-950/40 border border-emerald-500/30 rounded-xl p-3 px-4 flex items-center justify-between shadow-lg">
        <div className="flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <div>
            <span className="text-xs font-bold text-emerald-300 uppercase tracking-wider">ARC Predict: Low Failure Risk ({risk_percent}%)</span>
            <p className="text-xs text-slate-400">Execution trajectory is stable. Context firewall quality high.</p>
          </div>
        </div>
        <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/30 font-mono">
          STABLE RUN
        </span>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-amber-950/80 via-rose-950/60 to-slate-900 border border-amber-500/40 rounded-xl p-4 flex items-center justify-between shadow-2xl animate-pulse">
      <div className="flex items-center gap-3.5">
        <div className="p-2.5 bg-amber-500/20 border border-amber-500/40 rounded-lg text-amber-400 shrink-0">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-black text-amber-300 uppercase tracking-wide flex items-center gap-1.5">
              ⚠️ ARC Predict: High Failure Probability ({risk_percent}%)
            </span>
          </div>
          <p className="text-xs text-slate-300 mt-0.5">
            <strong className="text-amber-200 font-semibold">Reason:</strong> {reason}
          </p>
        </div>
      </div>

      {preemptive_checkpoint && (
        <div className="flex items-center gap-2 shrink-0">
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/20 border border-amber-500/40 text-amber-300 text-xs font-semibold shadow-inner">
            <BookmarkPlus className="w-4 h-4 text-amber-400" />
            Pre-emptive Checkpoint Created
          </span>
        </div>
      )}
    </div>
  );
}
