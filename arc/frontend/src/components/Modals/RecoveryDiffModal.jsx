import React, { useState } from 'react';
import { X, RefreshCw, GitCommit, ArrowRight, Activity, Terminal, AlertOctagon, Check } from 'lucide-react';

export default function RecoveryDiffModal({ isOpen, onClose }) {
  const [activeTab, setActiveTab] = useState('diff');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#131316]/80 backdrop-blur-sm">
      <div className="w-full max-w-5xl bg-arc-surface border border-arc-outline rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="px-5 py-4 border-b border-arc-outline flex justify-between items-center bg-arc-bg">
          <div className="flex items-center gap-3">
            <div className="p-1.5 bg-arc-secondary/10 rounded border border-arc-secondary/20 text-arc-secondary">
              <RefreshCw className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-arc-textPrimary font-mono">Recovery Engine Rolled Back State</h2>
              <div className="text-[11px] text-arc-textSecondary font-mono mt-0.5 flex items-center gap-2">
                <span>Session ID: a1b2c3d4</span>
                <span className="w-1 h-1 rounded-full bg-arc-outline"></span>
                <span className="text-arc-error flex items-center gap-1"><AlertOctagon className="w-3 h-3"/> Syntax Error Detected at Step 5</span>
              </div>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 rounded-lg text-arc-textSecondary hover:bg-arc-outline hover:text-arc-textPrimary transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex flex-1 overflow-hidden font-mono">
          
          {/* Left Sidebar: Node Stepper / Checkpoints */}
          <div className="w-64 border-r border-arc-outline bg-arc-bg flex flex-col">
            <div className="px-4 py-3 border-b border-arc-outline text-xs font-semibold text-arc-textSecondary uppercase tracking-wider">
              Execution Checkpoints
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-0 relative">
              {/* Node connecting line */}
              <div className="absolute left-[1.35rem] top-6 bottom-8 w-px bg-arc-outline"></div>

              {[
                { step: 1, name: 'Init Session', status: 'success' },
                { step: 2, name: 'Fetch Schema', status: 'success' },
                { step: 3, name: 'Analyze Columns', status: 'success' },
                { step: 4, name: 'Generate SQL (Valid Checkpoint)', status: 'recovered', active: true },
                { step: 5, name: 'Execute Migration', status: 'failed' },
              ].map((node, i) => (
                <div key={node.step} className="relative flex gap-3 pb-6 group cursor-pointer">
                  <div className="relative z-10 w-4 h-4 rounded-full mt-0.5 border-2 flex items-center justify-center bg-arc-bg
                    ${node.status === 'success' ? 'border-arc-tertiary' : 
                      node.status === 'failed' ? 'border-arc-error' : 
                      node.status === 'recovered' ? 'border-arc-secondary' : 'border-arc-outline'}"
                  >
                    <div className={`w-1.5 h-1.5 rounded-full ${node.active ? 'bg-arc-secondary' : node.status === 'failed' ? 'bg-arc-error' : node.status === 'success' ? 'bg-arc-tertiary' : ''}`}></div>
                  </div>
                  <div className="flex-1">
                    <div className={`text-xs font-semibold ${node.active ? 'text-arc-secondary' : node.status === 'failed' ? 'text-arc-error' : 'text-arc-textPrimary'}`}>
                      Step {node.step}: {node.name}
                    </div>
                    {node.active && (
                      <div className="text-[10px] text-arc-textSecondary mt-1">Rollback target state loaded.</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Main Area: Diff Inspector & Logs */}
          <div className="flex-1 flex flex-col bg-arc-surface min-w-0">
            <div className="flex border-b border-arc-outline bg-arc-bg">
              <button 
                onClick={() => setActiveTab('diff')}
                className={`px-6 py-3 text-xs font-semibold uppercase tracking-wider transition-colors ${activeTab === 'diff' ? 'text-arc-secondary border-b-2 border-arc-secondary bg-arc-surface' : 'text-arc-textSecondary hover:text-arc-textPrimary'}`}
              >
                State Diff Inspector
              </button>
              <button 
                onClick={() => setActiveTab('trace')}
                className={`px-6 py-3 text-xs font-semibold uppercase tracking-wider transition-colors ${activeTab === 'trace' ? 'text-arc-secondary border-b-2 border-arc-secondary bg-arc-surface' : 'text-arc-textSecondary hover:text-arc-textPrimary'}`}
              >
                Failure Trace
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {activeTab === 'diff' ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-4 text-xs font-medium bg-arc-bg p-3 border border-arc-outline rounded-lg">
                    <div className="flex items-center gap-2 text-arc-error">
                      <GitCommit className="w-4 h-4"/>
                      <span className="line-through opacity-70">Faulty State (Step 5)</span>
                    </div>
                    <ArrowRight className="w-4 h-4 text-arc-textSecondary" />
                    <div className="flex items-center gap-2 text-arc-secondary">
                      <Check className="w-4 h-4"/>
                      <span>Restored Checkpoint (Step 4)</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-[1px] border border-arc-outline rounded-lg overflow-hidden bg-arc-outline">
                    <div className="bg-arc-bg flex flex-col">
                      <div className="px-3 py-2 bg-arc-error/10 border-b border-arc-outline text-xs text-arc-error font-semibold flex justify-between">
                        <span>Failed Execution (Post-state)</span>
                        <span className="opacity-60">database.sql</span>
                      </div>
                      <pre className="p-4 text-[11px] leading-relaxed text-arc-textSecondary overflow-x-auto flex-1">
                        <code>
                          <span className="opacity-50">1| </span>CREATE TABLE users (<br/>
                          <span className="opacity-50">2| </span>  id UUID PRIMARY KEY,<br/>
                          <span className="opacity-50">3| </span>  email VARCHAR(255) NOT NULL,<br/>
                          <span className="text-arc-error bg-arc-error/10 px-1 rounded block">4|   CREATE INDEX idx_email ON users(email) -- Syntax Error</span>
                          <span className="opacity-50">5| </span>);
                        </code>
                      </pre>
                    </div>
                    <div className="bg-arc-bg flex flex-col">
                      <div className="px-3 py-2 bg-arc-secondary/10 border-b border-arc-outline text-xs text-arc-secondary font-semibold flex justify-between">
                        <span>Restored State (Pre-execution)</span>
                        <span className="opacity-60">database.sql</span>
                      </div>
                      <pre className="p-4 text-[11px] leading-relaxed text-arc-textSecondary overflow-x-auto flex-1">
                        <code>
                          <span className="opacity-50">1| </span>CREATE TABLE users (<br/>
                          <span className="opacity-50">2| </span>  id UUID PRIMARY KEY,<br/>
                          <span className="opacity-50">3| </span>  email VARCHAR(255) NOT NULL<br/>
                          <span className="text-arc-tertiary bg-arc-tertiary/10 px-1 rounded block">4| );</span>
                          <span className="text-arc-tertiary bg-arc-tertiary/10 px-1 rounded block">5| CREATE INDEX idx_email ON users(email);</span>
                        </code>
                      </pre>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="bg-[#131316] border border-arc-error/30 rounded-lg p-4 font-mono text-xs">
                    <div className="flex items-center gap-2 mb-3 text-arc-error border-b border-arc-error/20 pb-2">
                      <Terminal className="w-4 h-4"/>
                      <span className="font-semibold">psycopg2.errors.SyntaxError: syntax error at or near "CREATE"</span>
                    </div>
                    <div className="text-arc-textSecondary space-y-1 opacity-80 leading-relaxed">
                      <p>Traceback (most recent call last):</p>
                      <p>  File "arc/backend/core/db.py", line 142, in execute_migration</p>
                      <p>    cursor.execute(sql_script)</p>
                      <p className="text-arc-error">psycopg2.errors.SyntaxError: syntax error at or near "CREATE"</p>
                      <p className="text-arc-error">LINE 4:   CREATE INDEX idx_email ON users(email)</p>
                      <p className="text-arc-error">          ^</p>
                    </div>
                  </div>
                  <div className="bg-arc-secondary/10 border border-arc-secondary/20 p-4 rounded-lg flex items-start gap-3">
                    <Activity className="w-5 h-5 text-arc-secondary shrink-0 mt-0.5" />
                    <div className="text-xs text-arc-textPrimary leading-relaxed">
                      <span className="font-semibold text-arc-secondary block mb-1">Recovery Engine Action</span>
                      Detected database execution failure. Automatically rolled back the session state to <strong>Step 4 Checkpoint</strong>. The agent has been re-prompted with the syntax error trace and instructed to correct the schema format before attempting execution again.
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            <div className="p-4 border-t border-arc-outline bg-arc-bg flex justify-end">
              <button 
                onClick={onClose}
                className="px-4 py-2 bg-arc-primary hover:bg-arc-primary/90 text-[#131316] text-xs font-bold rounded transition-colors"
              >
                Acknowledge Recovery
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
