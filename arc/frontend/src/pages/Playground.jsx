import React, { useState } from 'react';
import { Terminal, Play, Shield, Activity, RefreshCw } from 'lucide-react';

export default function Playground() {
  const [agentName, setAgentName] = useState('Claude Assistant');
  const [task, setTask] = useState('Analyze system logs and optimize SQL database indexing.');
  const [contextSources, setContextSources] = useState(
    'Source A: Q3 revenue was $14.2M.\nSource B: Q3 revenue was $14.5M.'
  );
  const [firewallThreshold, setFirewallThreshold] = useState(0.85);
  const [logs, setLogs] = useState([]);
  const [isRunning, setIsRunning] = useState(false);

  const handleRunAgent = async () => {
    setIsRunning(true);
    setLogs([]);
    
    const mockStream = [
      { type: 'info', text: `Initializing ARCRuntime session for agent '${agentName}'...` },
      { type: 'firewall', text: `Filtering context sources (Threshold: ${firewallThreshold})...` },
      { type: 'firewall', text: 'Conflict detected: [Numerical conflict between Source A and Source B]' },
      { type: 'flight', text: 'Step 1: Calling Claude (claude-sonnet-4-6)...' },
      { type: 'recovery', text: 'Creating Checkpoint step 1 (validation score: 1.0)' },
      { type: 'success', text: 'Execution complete. Response received with confidence: 0.91' },
    ];

    let currentStep = 0;
    const interval = setInterval(() => {
      if (currentStep < mockStream.length) {
        setLogs((prev) => [...prev, mockStream[currentStep]]);
        currentStep++;
      } else {
        clearInterval(interval);
        setIsRunning(false);
      }
    }, 600);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-arc-textPrimary font-mono flex items-center gap-2">
          <Terminal className="w-5 h-5 text-arc-primary" />
          AGENT RUNTIME PLAYGROUND
        </h2>
        <p className="text-xs text-arc-textSecondary mt-1">
          Test Claude agents directly with ARC reliability layers: Flight Recorder, Context Firewall, and Recovery Engine.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Controls */}
        <div className="bg-arc-surface border border-arc-outline rounded-xl p-5 space-y-4 shadow-lg">
          <div>
            <label className="block text-xs font-mono text-arc-textSecondary mb-1">AGENT NAME</label>
            <input
              type="text"
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              className="w-full bg-arc-bg border border-arc-outline rounded-lg px-3 py-2 text-xs font-mono text-arc-textPrimary focus:outline-none focus:border-arc-primary transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-arc-textSecondary mb-1">TASK PROMPT (PROMPT BUILDER)</label>
            <textarea
              rows={3}
              value={task}
              onChange={(e) => setTask(e.target.value)}
              className="w-full bg-arc-bg border border-arc-outline rounded-lg p-3 text-xs font-mono text-arc-textPrimary focus:outline-none focus:border-arc-primary transition-colors resize-none"
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-arc-textSecondary mb-1">RAW CONTEXT SOURCES</label>
            <textarea
              rows={4}
              value={contextSources}
              onChange={(e) => setContextSources(e.target.value)}
              className="w-full bg-arc-bg border border-arc-outline rounded-lg p-3 text-xs font-mono text-arc-textPrimary focus:outline-none focus:border-arc-primary transition-colors resize-none"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-mono text-arc-textSecondary">FIREWALL THRESHOLD</label>
              <span className="text-xs font-mono text-arc-primary">{firewallThreshold.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={firewallThreshold}
              onChange={(e) => setFirewallThreshold(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-arc-outline rounded-lg appearance-none cursor-pointer accent-arc-primary"
            />
            <p className="text-[10px] text-arc-textSecondary mt-1 text-right">
              Higher thresholds require stricter factual consistency.
            </p>
          </div>

          <button
            onClick={handleRunAgent}
            disabled={isRunning}
            className="w-full py-2.5 bg-arc-primary hover:bg-arc-primary/90 text-[#131316] font-mono text-xs font-semibold rounded-lg flex items-center justify-center space-x-2 transition-colors disabled:opacity-50"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>{isRunning ? 'Running Session...' : 'Run Agent with ARC Layer'}</span>
          </button>
        </div>

        {/* Execution Log */}
        <div className="bg-arc-surface border border-arc-outline rounded-xl p-5 flex flex-col font-mono text-xs shadow-lg">
          <div className="flex items-center justify-between pb-3 border-b border-arc-outline">
            <h3 className="text-xs font-semibold text-arc-textPrimary uppercase tracking-wider">
              Streaming Terminal Log
            </h3>
            {isRunning && <span className="text-[10px] text-arc-primary animate-pulse flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-arc-primary"></span> Receiving
            </span>}
          </div>

          <div className="flex-1 bg-arc-bg border border-arc-outline rounded-lg p-4 mt-3 space-y-2 overflow-y-auto max-h-[380px]">
            {logs.length === 0 ? (
              <span className="text-arc-textSecondary italic">Click "Run Agent with ARC Layer" to start trace streaming...</span>
            ) : (
              logs.map((log, idx) => (
                <div key={idx} className="flex items-start space-x-2 font-mono text-[11px] leading-relaxed">
                  <span className="text-arc-textSecondary font-semibold select-none">&gt;</span>
                  <span
                    className={
                      log.type === 'firewall'
                        ? 'text-arc-secondary'
                        : log.type === 'recovery'
                        ? 'text-arc-tertiary'
                        : log.type === 'success'
                        ? 'text-arc-tertiary font-bold'
                        : 'text-arc-textPrimary'
                    }
                  >
                    {log.text}
                  </span>
                </div>
              ))
            )}
            {isRunning && (
              <div className="flex items-center space-x-2 text-arc-textSecondary animate-pulse">
                <span>&gt;</span>
                <span className="w-2 h-4 bg-arc-textSecondary inline-block"></span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
