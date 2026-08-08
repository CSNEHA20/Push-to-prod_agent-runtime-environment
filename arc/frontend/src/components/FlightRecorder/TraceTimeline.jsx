import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  Terminal, 
  Cpu, 
  ChevronDown, 
  ChevronRight, 
  Clock, 
  AlertTriangle, 
  RotateCcw, 
  CheckCircle2, 
  XCircle,
  Copy,
  Check,
  Code2
} from 'lucide-react';

export default function TraceTimeline({ steps = [], currentStepIndex = 0, onSelectStep }) {
  const [expandedSteps, setExpandedSteps] = useState({});
  const [copiedKey, setCopiedKey] = useState(null);
  const stepRefs = useRef({});

  // Auto scroll current step into view when replaying
  useEffect(() => {
    if (stepRefs.current[currentStepIndex]) {
      stepRefs.current[currentStepIndex].scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      });
    }
  }, [currentStepIndex]);

  const toggleExpand = (index) => {
    setExpandedSteps(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const getTypeStyle = (type) => {
    switch (type?.toLowerCase()) {
      case 'llm_call':
      case 'llm':
        return {
          badge: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
          circle: 'bg-purple-500 text-white shadow-purple-500/30',
          label: 'LLM CALL',
          icon: Activity
        };
      case 'tool_call':
      case 'tool':
        return {
          badge: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
          circle: 'bg-blue-500 text-white shadow-blue-500/30',
          label: 'TOOL CALL',
          icon: Terminal
        };
      case 'decision':
      default:
        return {
          badge: 'bg-zinc-700/50 text-zinc-300 border-zinc-600/50',
          circle: 'bg-zinc-600 text-white shadow-zinc-600/30',
          label: 'DECISION',
          icon: Cpu
        };
    }
  };

  const getConfidenceColor = (score) => {
    if (score == null) return { bar: 'bg-zinc-600', text: 'text-zinc-400' };
    if (score >= 0.7) return { bar: 'bg-emerald-500', text: 'text-emerald-400' };
    if (score >= 0.4) return { bar: 'bg-amber-500', text: 'text-amber-400' };
    return { bar: 'bg-red-500', text: 'text-red-400' };
  };

  const formatDuration = (ms) => {
    if (ms == null) return '—';
    if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
    return `${ms}ms`;
  };

  if (!steps || steps.length === 0) {
    return (
      <div className="p-8 text-center bg-arc-surface/40 border border-arc-outline rounded-xl font-mono text-arc-textSecondary text-xs">
        <Activity className="w-8 h-8 text-arc-textSecondary mx-auto mb-2 opacity-50" />
        No trace steps recorded for this session.
      </div>
    );
  }

  return (
    <div className="relative pl-6 pr-2 py-4 space-y-6 font-mono text-xs">
      {/* Debugger Vertical Line */}
      <div className="absolute left-[35px] top-6 bottom-6 w-[2px] bg-arc-outline/60" />

      {steps.map((step, idx) => {
        const stepNum = step.step_number ?? (idx + 1);
        const isCurrent = currentStepIndex === idx;
        const isExpanded = expandedSteps[idx];
        const typeInfo = getTypeStyle(step.step_type);
        const IconComponent = typeInfo.icon;
        const confidenceInfo = getConfidenceColor(step.confidence_score);
        const isFailed = step.status === 'failed' || step.status === 'error';

        // Prepare JSON strings
        const inputDataStr = step.input_data ? JSON.stringify(step.input_data, null, 2) : 
                            (step.tool_input ? JSON.stringify(step.tool_input, null, 2) : null);
        const outputDataStr = step.output_data ? JSON.stringify(step.output_data, null, 2) : 
                             (step.tool_output ? JSON.stringify(step.tool_output, null, 2) : null);
        const contextStr = step.context_used ? JSON.stringify(step.context_used, null, 2) : null;

        return (
          <div 
            key={step.step_id || idx}
            ref={el => stepRefs.current[idx] = el}
            onClick={() => onSelectStep && onSelectStep(idx)}
            className="relative flex gap-4 group"
          >
            {/* Step Number Circle Badge */}
            <div className="relative z-10 shrink-0">
              <div 
                className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs shadow-md border border-white/10 transition-transform ${typeInfo.circle} ${
                  isCurrent ? 'ring-4 ring-arc-primary/30 scale-110' : ''
                }`}
              >
                {stepNum}
              </div>
            </div>

            {/* Step Debugger Card */}
            <div 
              className={`flex-1 bg-arc-surface border rounded-xl overflow-hidden transition-all duration-200 cursor-pointer ${
                isCurrent 
                  ? 'border-arc-primary ring-2 ring-arc-primary/20 shadow-lg shadow-arc-primary/10 animate-pulse-border' 
                  : isFailed
                  ? 'border-red-500/50 hover:border-red-400'
                  : 'border-arc-outline hover:border-arc-primary/50'
              }`}
            >
              {/* Card Header */}
              <div 
                onClick={(e) => {
                  e.stopPropagation();
                  toggleExpand(idx);
                }}
                className="p-3.5 flex flex-wrap items-center justify-between gap-3 bg-arc-bg/40 hover:bg-arc-bg/80 transition-colors"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  {/* Step Type Badge */}
                  <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider border flex items-center gap-1.5 ${typeInfo.badge}`}>
                    <IconComponent className="w-3 h-3" />
                    {typeInfo.label}
                  </span>

                  {/* Tool Name Badge if present */}
                  {step.tool_name && (
                    <span className="px-2 py-0.5 rounded bg-arc-outline text-arc-primary font-semibold text-[11px]">
                      {step.tool_name}
                    </span>
                  )}

                  {/* Recovered Badge */}
                  {step.was_recovered && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30 flex items-center gap-1">
                      <RotateCcw className="w-3 h-3" />
                      ↺ Recovered
                    </span>
                  )}

                  {/* Failed Badge */}
                  {isFailed && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-red-500/15 text-red-400 border border-red-500/30 flex items-center gap-1">
                      <XCircle className="w-3 h-3" />
                      ✕ Failed
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  {/* Duration Badge */}
                  <div className="flex items-center gap-1 text-[11px] text-arc-textSecondary bg-arc-bg border border-arc-outline px-2 py-0.5 rounded">
                    <Clock className="w-3 h-3 text-arc-textSecondary" />
                    <span>{formatDuration(step.duration_ms)}</span>
                  </div>

                  {/* Confidence Bar */}
                  {step.confidence_score != null && (
                    <div className="flex items-center gap-1.5 bg-arc-bg border border-arc-outline px-2 py-0.5 rounded min-w-[100px]">
                      <span className="text-[10px] text-arc-textSecondary font-medium">Conf:</span>
                      <div className="w-12 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${confidenceInfo.bar}`}
                          style={{ width: `${Math.min(100, Math.max(0, step.confidence_score * 100))}%` }}
                        />
                      </div>
                      <span className={`text-[10px] font-bold ${confidenceInfo.text}`}>
                        {(step.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}

                  {/* Expand Chevron */}
                  <div className="text-arc-textSecondary hover:text-arc-textPrimary">
                    {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </div>
                </div>
              </div>

              {/* Reasoning Summary Body */}
              {step.reasoning_summary && (
                <div className="px-4 py-2.5 border-t border-arc-outline/40 text-xs text-arc-textPrimary leading-relaxed bg-arc-surface">
                  <span className="text-arc-textSecondary text-[10px] uppercase font-semibold block mb-0.5 tracking-wider">
                    Reasoning
                  </span>
                  <p className="text-arc-textPrimary/90">{step.reasoning_summary}</p>
                </div>
              )}

              {/* Error Message display if present */}
              {step.error && (
                <div className="px-4 py-2 bg-red-950/30 border-t border-red-500/30 text-red-300 text-xs flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Error: </span>
                    {step.error}
                  </div>
                </div>
              )}

              {/* Expanded JSON Inspector Payload */}
              {isExpanded && (
                <div className="border-t border-arc-outline bg-arc-bg p-4 space-y-4">
                  <div className="flex items-center justify-between border-b border-arc-outline/60 pb-2">
                    <span className="text-xs font-bold text-arc-textPrimary flex items-center gap-1.5">
                      <Code2 className="w-4 h-4 text-arc-primary" />
                      DEBUG PAYLOAD INSPECTOR
                    </span>
                    <span className="text-[10px] text-arc-textSecondary">Step #{stepNum} Payload</span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Input Data */}
                    <div className="border border-arc-outline rounded-lg overflow-hidden bg-arc-surface">
                      <div className="px-3 py-1.5 bg-arc-bg/80 border-b border-arc-outline flex justify-between items-center text-[11px]">
                        <span className="font-semibold text-arc-primary uppercase tracking-wider">
                          Input Data
                        </span>
                        {inputDataStr && (
                          <button
                            onClick={() => copyToClipboard(inputDataStr, `in-${idx}`)}
                            className="text-arc-textSecondary hover:text-arc-textPrimary flex items-center gap-1 text-[10px]"
                          >
                            {copiedKey === `in-${idx}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                            {copiedKey === `in-${idx}` ? 'Copied' : 'Copy'}
                          </button>
                        )}
                      </div>
                      <pre className="p-3 text-[11px] font-mono text-zinc-300 overflow-x-auto max-h-60 leading-relaxed whitespace-pre-wrap">
                        {inputDataStr || <span className="text-zinc-600 italic">No input data recorded</span>}
                      </pre>
                    </div>

                    {/* Output Data */}
                    <div className="border border-arc-outline rounded-lg overflow-hidden bg-arc-surface">
                      <div className="px-3 py-1.5 bg-arc-bg/80 border-b border-arc-outline flex justify-between items-center text-[11px]">
                        <span className="font-semibold text-emerald-400 uppercase tracking-wider">
                          Output Data
                        </span>
                        {outputDataStr && (
                          <button
                            onClick={() => copyToClipboard(outputDataStr, `out-${idx}`)}
                            className="text-arc-textSecondary hover:text-arc-textPrimary flex items-center gap-1 text-[10px]"
                          >
                            {copiedKey === `out-${idx}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                            {copiedKey === `out-${idx}` ? 'Copied' : 'Copy'}
                          </button>
                        )}
                      </div>
                      <pre className="p-3 text-[11px] font-mono text-zinc-300 overflow-x-auto max-h-60 leading-relaxed whitespace-pre-wrap">
                        {outputDataStr || <span className="text-zinc-600 italic">No output data recorded</span>}
                      </pre>
                    </div>
                  </div>

                  {/* Optional Context Used */}
                  {contextStr && (
                    <div className="border border-arc-outline rounded-lg overflow-hidden bg-arc-surface">
                      <div className="px-3 py-1.5 bg-arc-bg/80 border-b border-arc-outline flex justify-between items-center text-[11px]">
                        <span className="font-semibold text-amber-400 uppercase tracking-wider">
                          Context Used
                        </span>
                        <button
                          onClick={() => copyToClipboard(contextStr, `ctx-${idx}`)}
                          className="text-arc-textSecondary hover:text-arc-textPrimary flex items-center gap-1 text-[10px]"
                        >
                          {copiedKey === `ctx-${idx}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                          {copiedKey === `ctx-${idx}` ? 'Copied' : 'Copy'}
                        </button>
                      </div>
                      <pre className="p-3 text-[11px] font-mono text-zinc-300 overflow-x-auto max-h-48 leading-relaxed whitespace-pre-wrap">
                        {contextStr}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
