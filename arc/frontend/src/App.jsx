import React, { useState, useEffect } from 'react';
import { Activity, Shield, RefreshCw, Radio, Terminal, Server, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function App() {
  const [healthStatus, setHealthStatus] = useState({ status: 'connecting', engines: {} });
  const [logs, setLogs] = useState([
    { id: 1, type: 'info', engine: 'System', message: 'ARC Dashboard initialized' },
    { id: 2, type: 'flight', engine: 'Flight Recorder', message: 'Awaiting active agent session stream...' },
    { id: 3, type: 'firewall', engine: 'Context Firewall', message: 'Rules engine active & validating...' },
    { id: 4, type: 'recovery', engine: 'Recovery Engine', message: 'Checkpoint storage standing by...' }
  ]);

  useEffect(() => {
    // Basic health status polling from FastAPI backend
    const checkHealth = async () => {
      try {
        const res = await fetch('http://localhost:8000/health');
        if (res.ok) {
          const data = await res.json();
          setHealthStatus(data);
        }
      } catch (err) {
        setHealthStatus({ status: 'offline', error: err.message });
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#0B0F19] text-slate-100 flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-800 bg-[#111827]/80 backdrop-blur sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-9 w-9 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/20">
            ARC
          </div>
          <div>
            <h1 className="font-bold text-lg leading-none">Agent Runtime Core</h1>
            <p className="text-xs text-slate-400 mt-1">Reliability Infrastructure for Claude Agents</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-full text-xs">
            <span className={`h-2.5 w-2.5 rounded-full ${healthStatus.status === 'healthy' ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`}></span>
            <span className="capitalize font-mono text-slate-300">
              Backend: {healthStatus.status || 'checking'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Dashboard Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {/* Engine Cards Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Flight Recorder */}
          <div className="bg-[#111827] border border-slate-800 rounded-xl p-5 hover:border-indigo-500/50 transition-all group">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-400 group-hover:bg-indigo-500 group-hover:text-white transition-colors">
                <Activity className="h-6 w-6" />
              </div>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Operational
              </span>
            </div>
            <h3 className="font-semibold text-lg">Flight Recorder</h3>
            <p className="text-sm text-slate-400 mt-1">
              Records every Claude API decision, tool execution, and context snapshot for full replay.
            </p>
          </div>

          {/* Context Firewall */}
          <div className="bg-[#111827] border border-slate-800 rounded-xl p-5 hover:border-amber-500/50 transition-all group">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-400 group-hover:bg-amber-500 group-hover:text-white transition-colors">
                <Shield className="h-6 w-6" />
              </div>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Operational
              </span>
            </div>
            <h3 className="font-semibold text-lg">Context Firewall</h3>
            <p className="text-sm text-slate-400 mt-1">
              Filters, validates, and catches conflicting data sources before sending prompts to Claude.
            </p>
          </div>

          {/* Recovery Engine */}
          <div className="bg-[#111827] border border-slate-800 rounded-xl p-5 hover:border-emerald-500/50 transition-all group">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400 group-hover:bg-emerald-500 group-hover:text-white transition-colors">
                <RefreshCw className="h-6 w-6" />
              </div>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Operational
              </span>
            </div>
            <h3 className="font-semibold text-lg">Recovery Engine</h3>
            <p className="text-sm text-slate-400 mt-1">
              Automated state checkpointing and instant state recovery from API or agent failures.
            </p>
          </div>
        </div>

        {/* Live Stream / Terminal Panel */}
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <Terminal className="h-5 w-5 text-blue-400" />
              <h2 className="font-semibold text-slate-200">Runtime Telemetry Stream</h2>
            </div>
            <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono">
              <Radio className="h-4 w-4 text-emerald-400 animate-pulse" />
              <span>LIVE LOGS</span>
            </div>
          </div>

          <div className="font-mono text-xs space-y-2 bg-[#090D16] p-4 rounded-lg border border-slate-800/80 max-h-72 overflow-y-auto">
            {logs.map((log) => (
              <div key={log.id} className="flex items-start space-x-3 border-b border-slate-900 pb-1.5 last:border-0">
                <span className="text-slate-500 select-none">[{new Date().toLocaleTimeString()}]</span>
                <span className={`px-1.5 py-0.5 rounded font-semibold text-[10px] uppercase ${
                  log.engine === 'Flight Recorder' ? 'bg-indigo-500/20 text-indigo-300' :
                  log.engine === 'Context Firewall' ? 'bg-amber-500/20 text-amber-300' :
                  log.engine === 'Recovery Engine' ? 'bg-emerald-500/20 text-emerald-300' :
                  'bg-blue-500/20 text-blue-300'
                }`}>
                  {log.engine}
                </span>
                <span className="text-slate-300">{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-4 text-center text-xs text-slate-500 mt-auto">
        ARC — Agent Runtime Core &copy; 2026. Built with FastAPI, React, PostgreSQL & Redis.
      </footer>
    </div>
  );
}
