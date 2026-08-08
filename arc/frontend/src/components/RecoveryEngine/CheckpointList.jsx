import React, { useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  CornerUpLeft, 
  ShieldCheck, 
  Clock, 
  Check, 
  Activity,
  AlertTriangle,
  RotateCcw
} from 'lucide-react';

/**
 * CheckpointList component
 * Displays horizontal visual timeline of step checkpoints, failure points, and amber recovery jump arrows.
 */
export default function CheckpointList({ steps = [], recoveryEvents = [] }) {
  const [hoveredStep, setHoveredStep] = useState(null);

  // Default sample steps if none provided
  const defaultSteps = [
    { step_number: 1, name: 'Initialization', status: 'completed', validation_score: 0.98, timestamp: '12:04:01', is_checkpoint: true },
    { step_number: 2, name: 'Context Analysis', status: 'completed', validation_score: 0.94, timestamp: '12:04:05', is_checkpoint: true },
    { step_number: 3, name: 'SQL Query Gen', status: 'failed', validation_score: 0.35, timestamp: '12:04:12', error: 'DatabaseError: Connection pool reset failure', is_checkpoint: false },
    { step_number: 4, name: 'Rollback & Patch', status: 'recovered', validation_score: 0.78, timestamp: '12:04:18', recovered_from_step: 3, rollback_target_step: 2, is_checkpoint: true },
    { step_number: 5, name: 'Execution Pass', status: 'completed', validation_score: 0.96, timestamp: '12:04:25', is_checkpoint: true }
  ];

  const timelineSteps = steps && steps.length > 0 ? steps : defaultSteps;

  // Identify failure steps and recovery jump targets
  const failureStep = timelineSteps.find(s => s.status === 'failed' || s.error);
  const recoveryStep = timelineSteps.find(s => s.status === 'recovered' || s.was_recovered || s.rollback_target_step);

  const failureIdx = failureStep ? timelineSteps.findIndex(s => s.step_number === failureStep.step_number) : -1;
  const targetIdx = recoveryStep && recoveryStep.rollback_target_step 
    ? timelineSteps.findIndex(s => s.step_number === recoveryStep.rollback_target_step) 
    : (failureIdx > 0 ? failureIdx - 1 : -1);

  return (
    <div className="bg-arc-surface border border-arc-outline rounded-xl p-5 font-mono space-y-6 shadow-sm">
      <div className="flex items-center justify-between border-b border-arc-outline pb-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-arc-tertiary" />
          <h3 className="text-sm font-bold text-arc-textPrimary uppercase tracking-wider">
            Checkpoint State Timeline & Rollback Jumps
          </h3>
        </div>
        <span className="text-xs text-arc-textSecondary">
          Recorded Steps: <strong className="text-arc-textPrimary">{timelineSteps.length}</strong>
        </span>
      </div>

      {/* Horizontal Timeline Track */}
      <div className="relative pt-8 pb-4 px-4 bg-arc-bg/70 border border-arc-outline/60 rounded-xl overflow-x-auto">
        {/* Recovery Amber Jump Arrow SVG overlay */}
        {failureIdx !== -1 && targetIdx !== -1 && failureIdx > targetIdx && (
          <div className="absolute top-2 left-0 right-0 pointer-events-none px-8 flex justify-between z-10">
            <div className="w-full relative h-8">
              <svg className="w-full h-full overflow-visible">
                <defs>
                  <marker
                    id="amber-arrow"
                    viewBox="0 0 10 10"
                    refX="6"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#f59e0b" />
                  </marker>
                </defs>

                {/* Curved dashed amber line connecting failed step back to target step */}
                <path
                  d={`M ${80 + failureIdx * 120} 24 Q ${80 + ((failureIdx + targetIdx) / 2) * 120} -5 ${80 + targetIdx * 120} 24`}
                  fill="none"
                  stroke="#f59e0b"
                  strokeWidth="2.5"
                  strokeDasharray="4 3"
                  markerEnd="url(#amber-arrow)"
                />
              </svg>
              <div 
                className="absolute text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/40 shadow-sm whitespace-nowrap"
                style={{
                  left: `${((targetIdx + failureIdx) / 2) * 18}%`,
                  top: '-12px',
                  transform: 'translateX(-50%)'
                }}
              >
                <span className="flex items-center gap-1">
                  <RotateCcw className="w-3 h-3" />
                  Rollback Jump (Step #{failureIdx + 1} ➔ #{targetIdx + 1})
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Timeline Node Items */}
        <div className="flex items-center justify-between min-w-[600px] relative z-0">
          {/* Base connecting background line */}
          <div className="absolute top-1/2 left-6 right-6 h-0.5 bg-arc-outline/60 -translate-y-1/2 z-0" />

          {timelineSteps.map((step, idx) => {
            const isFailed = step.status === 'failed' || step.error;
            const isRecovered = step.status === 'recovered' || step.was_recovered;
            const isTarget = targetIdx === idx;
            const valScore = typeof step.validation_score === 'number' 
              ? step.validation_score 
              : (step.confidence_score || 0.9);
            const scorePercent = Math.round(valScore * 100);

            return (
              <div
                key={step.step_number || idx}
                className="relative flex flex-col items-center group cursor-pointer z-10"
                onMouseEnter={() => setHoveredStep(step)}
                onMouseLeave={() => setHoveredStep(null)}
              >
                {/* Node Circle */}
                <div 
                  className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300 shadow-md ${
                    isFailed
                      ? 'bg-red-500/20 border-red-500 text-red-400 ring-4 ring-red-500/10 animate-bounce'
                      : isRecovered
                      ? 'bg-amber-500/20 border-amber-500 text-amber-400 ring-4 ring-amber-500/10'
                      : isTarget
                      ? 'bg-emerald-500/20 border-emerald-400 text-emerald-400 ring-4 ring-emerald-500/20'
                      : 'bg-arc-surface border-emerald-500/80 text-emerald-400 hover:border-emerald-400'
                  }`}
                >
                  {isFailed ? (
                    <XCircle className="w-5 h-5 text-red-400" />
                  ) : isRecovered ? (
                    <RotateCcw className="w-5 h-5 text-amber-400" />
                  ) : (
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  )}
                </div>

                {/* Step Number & Title */}
                <div className="mt-2 text-center">
                  <span className="text-[11px] font-bold text-arc-textPrimary block">
                    Step #{step.step_number || idx + 1}
                  </span>
                  <span className="text-[10px] text-arc-textSecondary block truncate max-w-[90px]">
                    {step.name || step.tool_name || (isFailed ? 'Failure' : 'Checkpoint')}
                  </span>
                </div>

                {/* Hover Tooltip */}
                <div className="absolute bottom-full mb-3 hidden group-hover:flex flex-col bg-arc-surface border border-arc-outline rounded-lg p-3 w-52 shadow-xl z-30 pointer-events-none text-xs font-mono">
                  <div className="flex items-center justify-between border-b border-arc-outline/60 pb-1.5 mb-1.5">
                    <span className="font-bold text-arc-textPrimary">
                      Step #{step.step_number || idx + 1} Metadata
                    </span>
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      isFailed ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'
                    }`}>
                      {isFailed ? 'FAILED' : 'VALID'}
                    </span>
                  </div>

                  <div className="space-y-1 text-[11px] text-arc-textSecondary">
                    <div className="flex justify-between">
                      <span>Timestamp:</span>
                      <strong className="text-arc-textPrimary">
                        {step.timestamp ? (step.timestamp.includes('T') ? new Date(step.timestamp).toLocaleTimeString() : step.timestamp) : 'N/A'}
                      </strong>
                    </div>

                    <div className="flex justify-between">
                      <span>Validation Score:</span>
                      <strong className={`font-bold ${scorePercent >= 80 ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {scorePercent}%
                      </strong>
                    </div>

                    {isFailed && step.error && (
                      <div className="pt-1 mt-1 border-t border-red-500/20 text-red-300 text-[10px]">
                        <strong>Error:</strong> {step.error}
                      </div>
                    )}

                    {isTarget && (
                      <div className="pt-1 mt-1 border-t border-emerald-500/20 text-emerald-400 text-[10px] font-bold">
                        ✓ Checkpoint Safe Rollback State Target
                      </div>
                    )}
                  </div>

                  {/* Tooltip caret */}
                  <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-arc-surface" />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
