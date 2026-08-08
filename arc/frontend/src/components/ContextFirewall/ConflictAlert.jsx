import React from 'react';
import { 
  AlertTriangle, 
  CheckCircle2, 
  ShieldAlert, 
  FileText, 
  ArrowRightLeft,
  Check,
  AlertOctagon,
  Info
} from 'lucide-react';

/**
 * ConflictAlert component
 * Lists all context conflicts detected by the Context Firewall.
 * Each card shows severity badge, conflict type, description, resolution,
 * and the two conflicting sources side-by-side.
 * Sorted by severity (critical first).
 * If no conflicts exist, renders a green "✓ No conflicts detected" banner.
 */
export default function ConflictAlert({ conflicts = [] }) {
  // Severity rank mapping for sorting
  const severityOrder = {
    critical: 1,
    high: 2,
    medium: 3,
    low: 4
  };

  const getSeverityBadge = (severity = 'medium') => {
    const lev = severity.toLowerCase();
    switch (lev) {
      case 'critical':
        return (
          <span className="px-2.5 py-0.5 rounded text-[11px] font-bold uppercase tracking-wide bg-red-500/15 text-red-400 border border-red-500/30 flex items-center gap-1">
            <AlertOctagon className="w-3.5 h-3.5" />
            CRITICAL
          </span>
        );
      case 'high':
        return (
          <span className="px-2.5 py-0.5 rounded text-[11px] font-bold uppercase tracking-wide bg-orange-500/15 text-orange-400 border border-orange-500/30 flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5" />
            HIGH SEVERITY
          </span>
        );
      case 'medium':
        return (
          <span className="px-2.5 py-0.5 rounded text-[11px] font-bold uppercase tracking-wide bg-amber-500/15 text-amber-400 border border-amber-500/30 flex items-center gap-1">
            <ShieldAlert className="w-3.5 h-3.5" />
            MEDIUM SEVERITY
          </span>
        );
      case 'low':
      default:
        return (
          <span className="px-2.5 py-0.5 rounded text-[11px] font-bold uppercase tracking-wide bg-gray-500/15 text-gray-400 border border-gray-500/30 flex items-center gap-1">
            <Info className="w-3.5 h-3.5" />
            LOW SEVERITY
          </span>
        );
    }
  };

  const getConflictTypeBadge = (type = 'Factual') => {
    const formattedType = type.charAt(0).toUpperCase() + type.slice(1).toLowerCase();
    return (
      <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-arc-primary/10 text-arc-primary border border-arc-primary/25">
        {formattedType} Conflict
      </span>
    );
  };

  // Sort conflicts by severity
  const sortedConflicts = [...conflicts].sort((a, b) => {
    const rankA = severityOrder[a.severity?.toLowerCase()] || 99;
    const rankB = severityOrder[b.severity?.toLowerCase()] || 99;
    return rankA - rankB;
  });

  // If no conflicts detected
  if (!conflicts || conflicts.length === 0) {
    return (
      <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-5 font-mono text-emerald-400 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-400">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-sm font-bold tracking-tight">✓ No conflicts detected</h3>
            <p className="text-xs text-emerald-300/80 mt-0.5">
              All retrieved context sources are semantically aligned and verified free of logical contradictions.
            </p>
          </div>
        </div>
        <span className="text-xs font-semibold px-3 py-1 bg-emerald-500/20 border border-emerald-500/30 rounded-full">
          0 Active Contradictions
        </span>
      </div>
    );
  }

  return (
    <div className="bg-arc-surface border border-arc-outline rounded-xl p-5 font-mono space-y-4">
      <div className="flex items-center justify-between border-b border-arc-outline pb-3">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-arc-error" />
          <h3 className="text-sm font-bold text-arc-textPrimary uppercase tracking-wider">
            Detected Semantic Conflicts ({sortedConflicts.length})
          </h3>
        </div>
        <span className="text-xs text-arc-textSecondary">
          Prioritized by Severity Risk
        </span>
      </div>

      <div className="space-y-4">
        {sortedConflicts.map((conflict, idx) => {
          const sourceA = conflict.sourceA || { name: conflict.source_a_id || 'Source A', snippet: conflict.source_a_text };
          const sourceB = conflict.sourceB || { name: conflict.source_b_id || 'Source B', snippet: conflict.source_b_text };

          return (
            <div 
              key={conflict.id || `conflict-${idx}`}
              className="bg-arc-bg border border-arc-outline hover:border-arc-error/40 rounded-xl p-4 transition-all shadow-sm space-y-3"
            >
              {/* Header Badges */}
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-arc-outline/60 pb-3">
                <div className="flex items-center gap-2 flex-wrap">
                  {getSeverityBadge(conflict.severity)}
                  {getConflictTypeBadge(conflict.type || conflict.conflict_type)}
                </div>
                {conflict.detected_at && (
                  <span className="text-[10px] text-arc-textSecondary">
                    Detected: {new Date(conflict.detected_at).toLocaleTimeString()}
                  </span>
                )}
              </div>

              {/* Description */}
              <div>
                <span className="text-[10px] text-arc-textSecondary uppercase tracking-wider block mb-1">
                  Conflict Description
                </span>
                <p className="text-xs text-arc-textPrimary leading-relaxed bg-arc-surface p-2.5 rounded border border-arc-outline/60">
                  {conflict.description}
                </p>
              </div>

              {/* Conflicting Sources Side by Side */}
              <div className="space-y-1.5">
                <span className="text-[10px] text-arc-textSecondary uppercase tracking-wider flex items-center gap-1">
                  <ArrowRightLeft className="w-3 h-3 text-arc-secondary" />
                  Conflicting Sources Comparison
                </span>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  {/* Source A Card */}
                  <div className="p-3 bg-arc-surface rounded-lg border border-arc-outline/80 space-y-1.5">
                    <div className="flex items-center justify-between border-b border-arc-outline/40 pb-1.5">
                      <span className="font-semibold text-arc-textPrimary flex items-center gap-1.5 truncate">
                        <FileText className="w-3.5 h-3.5 text-arc-primary" />
                        {sourceA.name || 'Source A'}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        Accepted
                      </span>
                    </div>
                    <p className="text-[11px] text-arc-textSecondary leading-relaxed italic">
                      "{sourceA.snippet || 'No source content snippet recorded.'}"
                    </p>
                  </div>

                  {/* Source B Card */}
                  <div className="p-3 bg-red-500/5 rounded-lg border border-red-500/30 space-y-1.5">
                    <div className="flex items-center justify-between border-b border-red-500/20 pb-1.5">
                      <span className="font-semibold text-arc-textPrimary flex items-center gap-1.5 truncate">
                        <FileText className="w-3.5 h-3.5 text-red-400" />
                        {sourceB.name || 'Source B'}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-red-500/15 text-red-400 border border-red-500/30">
                        Rejected
                      </span>
                    </div>
                    <p className="text-[11px] text-arc-textSecondary leading-relaxed italic">
                      "{sourceB.snippet || 'No source content snippet recorded.'}"
                    </p>
                  </div>
                </div>
              </div>

              {/* Resolution Taken */}
              {conflict.resolution && (
                <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/25 flex items-start gap-2 text-xs">
                  <Check className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-emerald-400 block">Resolution Taken:</span>
                    <span className="text-emerald-300/90">{conflict.resolution}</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
