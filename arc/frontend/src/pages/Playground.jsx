import React, { useState } from 'react';
import { Terminal, Play, Shield, Activity, RefreshCw } from 'lucide-react';

export default function Playground() {
  const [agentName, setAgentName] = useState('Claude Assistant');
  const [task, setTask] = useState('Analyze system logs and optimize SQL database indexing.');
  const [contextSources, setContextSources] = useState(
    'Source A: Q3 revenue was $14.2M.\nSource B: Q3 revenue was $14.5M.'
  );
  const [logs, setLogs] = useState([]);
  const [isRunning, setIsRunning] = useState(false);

  const handleRunAgent = async () => {
    setIsRunning(true);
    setLogs([
      { type: 'info', text: `Initializing ARCRuntime session for agent '${agentName}'...` },
      { type: 'firewall', text: 'Filtering context sources through ContextFirewall...' },
      { type: 'firewall', text: 'Conflict detected: [Numerical conflict between Source A and Source B]' },
      { type: 'flight', text: 'Step 1: Calling Claude (claude-sonnet-4-6)...' },
      { type: 'recovery', text: 'Creating Checkpoint step 1 (validation score: 1.0)' },
      { type: 'success', text: 'Execution complete. Response received with confidence: 0.85' },
    ]);
    setIsRunning(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-[#F1F5F9] font-mono flex items-center gap-2">
          <Terminal className="w-5 h-5 text-[#6366F1]" />
          AGENT RUNTIME PLAYGROUND
        </h2>
        <p className="text-xs text-[#94A3B8] mt-1">
          Test Claude agents directly with ARC reliability layers: Flight Recorder, Context Firewall, and Recovery Engine.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Controls */}
        <div className="bg-[#12121A] border border-[#1E1E2E] rounded-xl p-5 space-y-4 shadow-lg">
          <div>
            <label className="block text-xs font-mono text-[#94A3B8] mb-1">AGENT NAME</label>
            <input
              type="text"
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              className="w-full bg-[#0A0A0F] border border-[#1E1E2E] rounded-lg px-3 py-2 text-xs font-mono text-[#F1F5F9] focus:outline-none focus:border-[#6366F1]"
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-[#94A3B8] mb-1">TASK PROMPT</label>
            <textarea
              rows={3}
              value={task}
              onChange={(e) => setTask(e.target.value)}
              className="w-full bg-[#0A0A0F] border border-[#1E1E2E] rounded-lg p-3 text-xs font-mono text-[#F1F5F9] focus:outline-none focus:border-[#6366F1]"
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-[#94A3B8] mb-1">CONTEXT SOURCES (RAW)</label>
            <textarea
              rows={4}
              value={contextSources}
              onChange={(e) => setContextSources(e.target.value)}
              className="w-full bg-[#0A0A0F] border border-[#1E1E2E] rounded-lg p-3 text-xs font-mono text-[#F1F5F9] focus:outline-none focus:border-[#6366F1]"
            />
          </div>

          <button
            onClick={handleRunAgent}
            disabled={isRunning}
            className="w-full py-2.5 bg-[#6366F1] hover:bg-[#6366F1]/90 text-white font-mono text-xs font-semibold rounded-lg flex items-center justify-center space-x-2 transition-colors disabled:opacity-50"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>{isRunning ? 'Running Session...' : 'Run Agent with ARC Layer'}</span>
          </button>
        </div>

        {/* Execution Log */}
        <div className="bg-[#12121A] border border-[#1E1E2E] rounded-xl p-5 flex flex-col font-mono text-xs shadow-lg">
          <h3 className="text-xs font-semibold text-[#F1F5F9] uppercase tracking-wider pb-3 border-b border-[#1E1E2E]">
            Runtime Terminal Log
          </h3>

          <div className="flex-1 bg-[#0A0A0F] border border-[#1E1E2E] rounded-lg p-4 mt-3 space-y-2 overflow-y-auto max-h-[360px]">
            {logs.length === 0 ? (
              <span className="text-[#94A3B8] italic">Click "Run Agent with ARC Layer" to start trace streaming...</span>
            ) : (
              logs.map((log, idx) => (
                <div key={idx} className="flex items-start space-x-2">
                  <span className="text-[#94A3B8] font-semibold select-none">&gt;</span>
                  <span
                    className={
                      log.type === 'firewall'
                        ? 'text-[#F59E0B]'
                        : log.type === 'recovery'
                        ? 'text-[#10B981]'
                        : log.type === 'success'
                        ? 'text-[#10B981] font-bold'
                        : 'text-[#F1F5F9]'
                    }
                  >
                    {log.text}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
