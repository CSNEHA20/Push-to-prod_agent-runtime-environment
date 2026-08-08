import React, { useState, useEffect } from 'react';
import { GitCompare, X, AlertCircle, ArrowRight, CheckCircle } from 'lucide-react';

export default function ARCDiffViewer({ isOpen, onClose, defaultSessionId }) {
  const [sessionA, setSessionA] = useState(defaultSessionId || 'session-run-1');
  const [sessionB, setSessionB] = useState('session-run-2');
  const [diffData, setDiffData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchDiff();
    }
  }, [isOpen, sessionA, sessionB]);

  const fetchDiff = async () => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/sessions/diff/compare?session_a=${sessionA}&session_b=${sessionB}`);
      if (!res.ok) throw new Error('Diff fetch failed');
      const data = await res.json();
      setDiffData(data);
    } catch (e) {
      // Mock Fallback Diff Data for Demo
      setDiffData({
        session_a_id: "Run 1 (Baseline - Without ARC)",
        session_b_id: "Run 2 (Protected - With ARC)",
        divergence_step_index: 4,
        summary: "Divergence detected at Step 4: Confidence divergence: 54% vs 91%. Run 1 used unverified blog post context, while Run 2 filtered conflicting context via Context Firewall.",
        aligned_steps: [
          {
            step_index: 1,
            is_divergent: false,
            step_a: { decision: "Fetch company background", confidence: 0.95, context: "Official 10-K Filing" },
            step_b: { decision: "Fetch company background", confidence: 0.95, context: "Official 10-K Filing" }
          },
          {
            step_index: 2,
            is_divergent: false,
            step_a: { decision: "Analyze revenue metrics", confidence: 0.91, context: "Q3 Earnings Report" },
            step_b: { decision: "Analyze revenue metrics", confidence: 0.92, context: "Q3 Earnings Report" }
          },
          {
            step_index: 3,
            is_divergent: false,
            step_a: { decision: "Query external search tool", confidence: 0.88, context: "Search API query 'Q3 ARR'" },
            step_b: { decision: "Query external search tool", confidence: 0.89, context: "Search API query 'Q3 ARR'" }
          },
          {
            step_index: 4,
            is_divergent: true,
            diff_reasons: ["Context mismatch", "Confidence drop"],
            step_a: { decision: "Accepted unverified blog post ($980M)", confidence: 0.54, context: "Blog Unverified Data" },
            step_b: { decision: "Context Firewall flagged conflict -> Selected SEC report ($1.2B)", confidence: 0.93, context: "SEC Verified Audit" }
          },
          {
            step_index: 5,
            is_divergent: true,
            diff_reasons: ["Hallucinated report figure"],
            step_a: { decision: "Generated report with wrong revenue ($980M)", confidence: 0.48, context: "Hallucinated Context" },
            step_b: { decision: "Generated accurate report ($1.2B)", confidence: 0.96, context: "Curated Provenance Context" }
          }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-6">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-5xl h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/20 border border-purple-500/30 rounded-lg text-purple-400">
              <GitCompare className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                ARC Diff
                <span className="text-[10px] bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded border border-purple-500/30">
                  SIDE-BY-SIDE TRACE COMPARISON
                </span>
              </h2>
              <p className="text-xs text-slate-400">Compare execution runs, context divergence, and decision trees</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Divergence Alert Summary */}
        {diffData && (
          <div className="p-3 bg-purple-950/40 border-b border-purple-500/30 px-6 flex items-center gap-3 text-xs">
            <AlertCircle className="w-5 h-5 text-purple-400 shrink-0" />
            <div className="flex-1 text-slate-300">
              <strong className="text-purple-300 font-semibold">Divergence Summary:</strong> {diffData.summary}
            </div>
          </div>
        )}

        {/* Column Headers */}
        <div className="grid grid-cols-2 bg-slate-950 border-b border-slate-800 text-xs font-semibold text-slate-400">
          <div className="p-3 px-6 border-r border-slate-800 flex items-center justify-between">
            <span className="text-rose-400 font-mono">Run A: {diffData?.session_a_id}</span>
          </div>
          <div className="p-3 px-6 flex items-center justify-between">
            <span className="text-emerald-400 font-mono">Run B: {diffData?.session_b_id}</span>
          </div>
        </div>

        {/* Step Comparison Scrollable View */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 font-sans text-xs">
          {diffData?.aligned_steps.map((st) => (
            <div
              key={st.step_index}
              className={`grid grid-cols-2 rounded-xl border transition-all ${
                st.is_divergent
                  ? 'bg-rose-950/20 border-rose-500/40 shadow-lg'
                  : 'bg-slate-950/40 border-slate-800/60'
              }`}
            >
              {/* Run A Step */}
              <div className="p-4 border-r border-slate-800 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-mono text-[10px] bg-slate-900 px-2 py-0.5 rounded text-slate-400 border border-slate-800">
                    Step {st.step_index}
                  </span>
                  {st.step_a && (
                    <span className="font-mono text-[10px] text-slate-400">
                      Conf: {intVal(st.step_a.confidence)}%
                    </span>
                  )}
                </div>
                <p className="font-medium text-slate-200">{st.step_a?.decision || 'No step recorded'}</p>
                {st.step_a?.context && (
                  <div className="p-2 bg-slate-900 rounded border border-slate-800 text-[11px] text-slate-400">
                    Context: {st.step_a.context}
                  </div>
                )}
              </div>

              {/* Run B Step */}
              <div className="p-4 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-mono text-[10px] bg-slate-900 px-2 py-0.5 rounded text-slate-400 border border-slate-800">
                    Step {st.step_index}
                  </span>
                  {st.step_b && (
                    <span className="font-mono text-[10px] text-emerald-400 font-bold">
                      Conf: {intVal(st.step_b.confidence)}%
                    </span>
                  )}
                </div>
                <p className="font-medium text-slate-200">{st.step_b?.decision || 'No step recorded'}</p>
                {st.step_b?.context && (
                  <div className="p-2 bg-slate-900 rounded border border-emerald-500/30 text-[11px] text-emerald-300">
                    Context: {st.step_b.context}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function intVal(val) {
  if (val == null) return 0;
  return Math.round(val * 100);
}
