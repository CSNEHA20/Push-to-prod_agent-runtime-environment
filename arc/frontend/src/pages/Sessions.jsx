import React, { useState } from 'react';
import { Layers, Search, Filter, Play, Pause, FastForward, Rewind, Activity, ShieldAlert, CheckCircle2, ChevronRight, Terminal } from 'lucide-react';
import AgentCard from '../components/Dashboard/AgentCard';

export default function Sessions({ onSelectSession }) {
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [timelineStep, setTimelineStep] = useState(3);

  const [sessions] = useState([
    {
      session_id: 'a1b2c3d4-8899-0011-2233-445566778899',
      agent_name: 'Claude Code Synthesizer',
      task: 'Refactoring async session handler and optimizing SQL database queries for PostgreSQL',
      status: 'running',
      total_steps: 12,
      duration: '1m 24s',
    },
    {
      session_id: 'b2c3d4e5-9900-1122-3344-556677889900',
      agent_name: 'Context Firewall Evaluator',
      task: 'Scanning multi-source documentation for semantic contradictions and provenance tagging',
      status: 'recovered',
      total_steps: 8,
      duration: '45s',
    },
  ]);

  const mockTraces = [
    { step: 1, type: 'tool_call', name: 'search_codebase', content: 'Searching for "async_session_handler"' },
    { step: 2, type: 'agent_thought', content: 'Found the handler in core/db.py. I need to modify the connection pool settings.' },
    { step: 3, type: 'firewall_alert', name: 'Context Conflict', content: 'Blocked unverified connection string format detected in proposed edit.' },
    { step: 4, type: 'tool_call', name: 'edit_file', content: 'Applying verified rollback diff to core/db.py' },
  ];

  const filteredSessions = sessions.filter(s => {
    const matchesSearch = s.agent_name.toLowerCase().includes(search.toLowerCase()) ||
                          s.task.toLowerCase().includes(search.toLowerCase());
    const matchesFilter = filterStatus === 'all' || s.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  const selectedSession = sessions.find(s => s.session_id === selectedSessionId);

  return (
    <div className="flex h-full gap-6">
      {/* Left Pane: Session List */}
      <div className={`flex flex-col gap-4 transition-all duration-300 ${selectedSessionId ? 'w-1/3' : 'w-full'}`}>
        <div>
          <h2 className="text-xl font-bold text-arc-textPrimary font-mono flex items-center gap-2">
            <Layers className="w-5 h-5 text-arc-primary" />
            AGENT SESSIONS
          </h2>
          {!selectedSessionId && (
            <p className="text-xs text-arc-textSecondary mt-1">
              Inspect trace history, context filtering decisions, and checkpoint recovery records.
            </p>
          )}
        </div>

        <div className="flex flex-col xl:flex-row items-center justify-between gap-4 bg-arc-surface border border-arc-outline p-4 rounded-xl">
          <div className="relative w-full">
            <Search className="w-4 h-4 text-arc-textSecondary absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-arc-bg border border-arc-outline rounded-lg pl-9 pr-4 py-2 text-xs font-mono text-arc-textPrimary focus:outline-none focus:border-arc-primary transition-colors"
            />
          </div>

          {!selectedSessionId && (
            <div className="flex items-center space-x-2 w-full xl:w-auto font-mono text-xs overflow-x-auto">
              <Filter className="w-4 h-4 text-arc-textSecondary shrink-0" />
              {['all', 'running', 'recovered', 'failed'].map((status) => (
                <button
                  key={status}
                  onClick={() => setFilterStatus(status)}
                  className={`px-3 py-1.5 rounded-lg border capitalize transition-colors shrink-0 ${
                    filterStatus === status
                      ? 'bg-arc-primary/10 text-arc-primary border-arc-primary/30 font-semibold'
                      : 'bg-arc-bg text-arc-textSecondary border-arc-outline hover:text-arc-textPrimary'
                  }`}
                >
                  {status}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className={`grid gap-4 overflow-y-auto pr-2 ${selectedSessionId ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'}`}>
          {filteredSessions.map((agent) => (
            <div key={agent.session_id} onClick={() => setSelectedSessionId(agent.session_id)}>
              <AgentCard agent={agent} />
            </div>
          ))}
        </div>
      </div>

      {/* Right Pane: Deep-Dive Trace Viewer & Replay Timeline */}
      {selectedSessionId && (
        <div className="w-2/3 bg-arc-surface border border-arc-outline rounded-xl flex flex-col overflow-hidden shadow-xl">
          {/* Header */}
          <div className="p-4 border-b border-arc-outline bg-arc-bg/50 flex justify-between items-center">
            <div>
              <h3 className="font-bold text-arc-textPrimary font-mono">{selectedSession?.agent_name}</h3>
              <p className="text-xs text-arc-textSecondary font-mono mt-1">ID: {selectedSessionId}</p>
            </div>
            <button
              onClick={() => setSelectedSessionId(null)}
              className="text-xs font-mono text-arc-textSecondary hover:text-arc-textPrimary px-3 py-1 border border-arc-outline rounded hover:bg-arc-outline"
            >
              Close
            </button>
          </div>

          {/* Trace Viewer (Scrollable) */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 font-mono text-sm bg-[#131316]">
            {mockTraces.slice(0, timelineStep).map((trace, idx) => (
              <div key={idx} className="flex gap-4 p-3 rounded-lg border border-arc-outline/50 bg-arc-surface">
                <div className="shrink-0 w-8 h-8 rounded bg-arc-bg flex items-center justify-center border border-arc-outline text-arc-textSecondary">
                  {trace.step}
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    {trace.type === 'tool_call' && <Terminal className="w-4 h-4 text-arc-primary" />}
                    {trace.type === 'agent_thought' && <Activity className="w-4 h-4 text-arc-secondary" />}
                    {trace.type === 'firewall_alert' && <ShieldAlert className="w-4 h-4 text-arc-error" />}
                    <span className="font-semibold text-arc-textPrimary capitalize text-xs">
                      {trace.type.replace('_', ' ')}
                    </span>
                    {trace.name && (
                      <span className="text-[10px] bg-arc-outline px-1.5 py-0.5 rounded text-arc-textSecondary">
                        {trace.name}
                      </span>
                    )}
                  </div>
                  <p className="text-arc-textSecondary text-xs leading-relaxed">{trace.content}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Step Replay Timeline Slider */}
          <div className="p-4 border-t border-arc-outline bg-arc-surface">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-mono text-arc-textSecondary uppercase tracking-wider font-semibold">
                Trace Replay Timeline
              </span>
              <span className="text-xs font-mono text-arc-primary font-bold">
                Step {timelineStep} / {mockTraces.length}
              </span>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <button className="p-1.5 rounded hover:bg-arc-outline text-arc-textSecondary transition-colors" onClick={() => setTimelineStep(1)}>
                  <Rewind className="w-4 h-4" />
                </button>
                <button
                  className="p-2 rounded-full bg-arc-primary text-[#131316] hover:bg-arc-primary/90 transition-colors"
                  onClick={() => setIsPlaying(!isPlaying)}
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                </button>
                <button className="p-1.5 rounded hover:bg-arc-outline text-arc-textSecondary transition-colors" onClick={() => setTimelineStep(mockTraces.length)}>
                  <FastForward className="w-4 h-4" />
                </button>
              </div>
              
              <input
                type="range"
                min="1"
                max={mockTraces.length}
                value={timelineStep}
                onChange={(e) => setTimelineStep(parseInt(e.target.value))}
                className="flex-1 h-2 bg-arc-outline rounded-lg appearance-none cursor-pointer accent-arc-primary"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
