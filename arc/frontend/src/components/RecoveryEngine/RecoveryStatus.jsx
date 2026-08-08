import React from 'react';
import { 
  ShieldAlert, 
  Activity, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  RefreshCw, 
  ArrowRight, 
  Clock, 
  RotateCcw,
  Zap
} from 'lucide-react';

/**
 * RecoveryStatus component
 * Renders summary metrics card (Total checkpoints, failures detected, recovery rate, health badge)
 * and failure breakdown cards (failure type, error message, recovered step arrow, steps lost, recovery time).
 */
export default function RecoveryStatus({
  checkpointsSaved = 5,
  failuresDetected = 1,
  recoverySuccessRate = 100,
  healthStatus = 'Healthy', // 'Healthy' | 'Degraded' | 'Failed'
  failures = []
}) {
  // Default mock failure item if none provided
  const defaultFailures = [
    {
      id: 'fail-1',
      failure_type: 'Syntax/Parameter Exception',
      error_message: 'DatabaseError: Connection refused (invalid pool parameter max_overflow=NaN)',
      failed_at_step: 3,
      recovered_at_step: 4,
      rollback_checkpoint_step: 2,
      steps_lost: 1,
      recovery_time_ms: 650,
      status: 'recovered'
    }
  ];

  const failureList = failures && failures.length > 0 ? failures : defaultFailures;

  const getHealthBadge = (status = 'Healthy') => {
    const stat = status.toLowerCase();
    if (stat === 'healthy') {
      return (
        <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 shadow-sm">
          <CheckCircle2 className="w-4 h-4" />
          Healthy System State
        </span>
      );
    }
    if (stat === 'degraded') {
      return (
        <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 flex items-center gap-1.5 shadow-sm">
          <AlertTriangle className="w-4 h-4" />
          Degraded (Recovering)
        </span>
      );
    }
    return (
      <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-red-500/15 text-red-400 border border-red-500/30 flex items-center gap-1.5 shadow-sm">
        <XCircle className="w-4 h-4" />
        Critical Engine Failure
      </span>
    );
  };

  return (
    <div className="space-y-6 font-mono">
      {/* Top Summary Card */}
      <div className="bg-arc-surface border border-arc-outline rounded-xl p-5 space-y-4 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-arc-outline pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-arc-tertiary/15 rounded-xl border border-arc-tertiary/30 text-arc-tertiary shadow-sm">
              <RefreshCw className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-arc-textPrimary">Recovery Engine Health Metrics</h3>
              <p className="text-xs text-arc-textSecondary mt-0.5">
                Deterministic checkpoint snapshots & automated step rollback metrics.
              </p>
            </div>
          </div>

          <div>{getHealthBadge(healthStatus)}</div>
        </div>

        {/* 4 Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div className="bg-arc-bg border border-arc-outline p-3.5 rounded-lg">
            <span className="text-arc-textSecondary block mb-1">Total Checkpoints Saved</span>
            <span className="text-2xl font-extrabold text-arc-textPrimary">{checkpointsSaved}</span>
          </div>

          <div className="bg-arc-bg border border-amber-500/30 p-3.5 rounded-lg">
            <span className="text-arc-textSecondary block mb-1">Failures Intercepted</span>
            <span className="text-2xl font-extrabold text-amber-400">{failuresDetected}</span>
          </div>

          <div className="bg-arc-bg border border-emerald-500/30 p-3.5 rounded-lg">
            <span className="text-arc-textSecondary block mb-1">Recovery Success Rate</span>
            <span className="text-2xl font-extrabold text-emerald-400">{recoverySuccessRate}%</span>
          </div>

          <div className="bg-arc-bg border border-arc-outline p-3.5 rounded-lg">
            <span className="text-arc-textSecondary block mb-1">Engine Operational Mode</span>
            <span className="text-sm font-bold text-arc-tertiary mt-1 block">Active Auto-Rollback</span>
          </div>
        </div>
      </div>

      {/* Failures Section Below */}
      <div className="bg-arc-surface border border-arc-outline rounded-xl p-5 space-y-4 shadow-sm">
        <div className="flex items-center justify-between border-b border-arc-outline pb-3">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-amber-400" />
            <h3 className="text-sm font-bold text-arc-textPrimary uppercase tracking-wider">
              Intercepted Failures & Recovery Actions ({failureList.length})
            </h3>
          </div>
          <span className="text-xs text-arc-textSecondary">
            Auto-Mitigation Log
          </span>
        </div>

        {failureList.length > 0 ? (
          <div className="space-y-4">
            {failureList.map((fail, idx) => {
              const isRecovered = fail.status === 'recovered' || fail.recovered_at_step;

              return (
                <div
                  key={fail.id || `fail-${idx}`}
                  className="bg-arc-bg border border-arc-outline hover:border-amber-500/40 rounded-xl p-4 transition-all shadow-sm space-y-3"
                >
                  {/* Top Badges Row */}
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-arc-outline/60 pb-2.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        {fail.failure_type || 'Agent Execution Failure'}
                      </span>

                      {isRecovered ? (
                        <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          RECOVERED
                        </span>
                      ) : (
                        <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-red-500/15 text-red-400 border border-red-500/30 flex items-center gap-1">
                          <XCircle className="w-3.5 h-3.5" />
                          UNRESOLVED
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3 text-[11px] text-arc-textSecondary">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-arc-primary" />
                        Recovery Time: <strong className="text-arc-textPrimary">{fail.recovery_time_ms || 650}ms</strong>
                      </span>
                    </div>
                  </div>

                  {/* Error Message */}
                  <div>
                    <span className="text-[10px] text-arc-textSecondary uppercase tracking-wider block mb-1">
                      Error Exception Output
                    </span>
                    <p className="text-xs text-red-300 font-mono leading-relaxed bg-red-500/10 p-2.5 rounded border border-red-500/25">
                      {fail.error_message}
                    </p>
                  </div>

                  {/* Recovered from Step X Arrow */}
                  {isRecovered && (
                    <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/25 flex flex-wrap items-center justify-between gap-3 text-xs">
                      <div className="flex items-center gap-2 font-bold text-emerald-400">
                        <RotateCcw className="w-4 h-4" />
                        <span>Recovered from Step #{fail.failed_at_step || 3}</span>
                        <ArrowRight className="w-4 h-4 text-emerald-400" />
                        <span>Restored Checkpoint Step #{fail.rollback_checkpoint_step || 2}</span>
                      </div>

                      <div className="flex items-center gap-3 text-[11px] font-semibold text-emerald-300">
                        <span>Steps Lost: <strong className="text-amber-400">{fail.steps_lost ?? 1} step</strong></span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-8 text-center text-emerald-400 text-xs bg-emerald-500/5 rounded-xl border border-emerald-500/20">
            ✓ Zero failures recorded in this execution session.
          </div>
        )}
      </div>
    </div>
  );
}
