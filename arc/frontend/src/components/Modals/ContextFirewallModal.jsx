import React from 'react';
import { X, ShieldAlert, GitCommit, FileText, Check, AlertTriangle } from 'lucide-react';

export default function ContextFirewallModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#131316]/80 backdrop-blur-sm">
      <div className="w-full max-w-4xl bg-arc-surface border border-arc-outline rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="px-5 py-4 border-b border-arc-outline flex justify-between items-center bg-arc-bg">
          <div className="flex items-center gap-3">
            <div className="p-1.5 bg-arc-error/10 rounded border border-arc-error/20 text-arc-error">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-arc-textPrimary font-mono">Context Firewall Intervention</h2>
              <p className="text-[11px] text-arc-textSecondary font-mono mt-0.5">
                Blocked prompt execution due to critical semantic conflict in retrieved context.
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 rounded-lg text-arc-textSecondary hover:bg-arc-outline hover:text-arc-textPrimary transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1 font-mono">
          <div className="mb-6">
            <h3 className="text-xs font-semibold text-arc-textSecondary uppercase tracking-wider mb-2">
              Conflict Summary
            </h3>
            <div className="p-3 rounded-lg bg-arc-error/5 border border-arc-error/20 flex gap-3 text-sm text-arc-textPrimary">
              <AlertTriangle className="w-5 h-5 text-arc-error shrink-0" />
              <p>
                A severe numerical discrepancy was detected across retrieved documentation sources regarding <strong className="text-arc-error font-medium">Q3 2025 User Growth metrics</strong>. Passing conflicting context to the agent carries a 94% hallucination risk.
              </p>
            </div>
          </div>

          <h3 className="text-xs font-semibold text-arc-textSecondary uppercase tracking-wider mb-3">
            Provenance Comparison Matrix
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Source A */}
            <div className="border border-arc-outline rounded-lg bg-arc-bg flex flex-col">
              <div className="px-4 py-2 border-b border-arc-outline bg-arc-surface/50 flex justify-between items-center">
                <span className="text-xs font-bold text-arc-textPrimary flex items-center gap-2">
                  <FileText className="w-4 h-4 text-arc-textSecondary" />
                  Source A (Primary DB)
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] bg-arc-tertiary/10 text-arc-tertiary border border-arc-tertiary/20">
                  Confidence: High
                </span>
              </div>
              <div className="p-4 flex-1">
                <div className="text-xs text-arc-textSecondary mb-2 flex items-center gap-1.5">
                  <GitCommit className="w-3.5 h-3.5" /> Commit: <span className="text-arc-textPrimary">2f4a91b (2h ago)</span>
                </div>
                <div className="p-3 bg-arc-surface border border-arc-outline rounded text-sm text-arc-textPrimary leading-relaxed">
                  "Based on our final audit, the total user growth for Q3 2025 reached <span className="bg-arc-tertiary/20 text-arc-tertiary px-1 py-0.5 rounded border border-arc-tertiary/30">14.2 Million</span> active accounts."
                </div>
              </div>
              <div className="px-4 py-3 border-t border-arc-outline bg-arc-surface/30">
                <button className="w-full flex items-center justify-center gap-2 text-xs py-1.5 rounded border border-arc-outline hover:bg-arc-outline text-arc-textPrimary transition-colors">
                  <Check className="w-3.5 h-3.5 text-arc-tertiary" /> Approve Source
                </button>
              </div>
            </div>

            {/* Source B */}
            <div className="border border-arc-error/40 rounded-lg bg-arc-bg flex flex-col shadow-[0_0_15px_-3px_rgba(239,68,68,0.1)]">
              <div className="px-4 py-2 border-b border-arc-error/30 bg-arc-error/5 flex justify-between items-center">
                <span className="text-xs font-bold text-arc-textPrimary flex items-center gap-2">
                  <FileText className="w-4 h-4 text-arc-textSecondary" />
                  Source B (Confluence Draft)
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] bg-arc-error/10 text-arc-error border border-arc-error/20">
                  Confidence: Low
                </span>
              </div>
              <div className="p-4 flex-1">
                <div className="text-xs text-arc-textSecondary mb-2 flex items-center gap-1.5">
                  <GitCommit className="w-3.5 h-3.5" /> Updated: <span className="text-arc-textPrimary">Last week</span>
                </div>
                <div className="p-3 bg-arc-surface border border-arc-error/20 rounded text-sm text-arc-textPrimary leading-relaxed">
                  "Preliminary estimates show Q3 2025 user growth at around <span className="bg-arc-error/20 text-arc-error px-1 py-0.5 rounded border border-arc-error/30">14.5 Million</span> accounts, subject to revision."
                </div>
              </div>
              <div className="px-4 py-3 border-t border-arc-error/30 bg-arc-error/5">
                <button className="w-full flex items-center justify-center gap-2 text-xs py-1.5 rounded border border-arc-error/30 bg-arc-error/10 hover:bg-arc-error/20 text-arc-error transition-colors">
                  <X className="w-3.5 h-3.5" /> Reject Source
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
