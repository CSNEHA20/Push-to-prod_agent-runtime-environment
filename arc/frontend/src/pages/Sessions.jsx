import React, { useState } from 'react';
import { Layers, Search, Filter, ExternalLink } from 'lucide-react';
import AgentCard from '../components/Dashboard/AgentCard';

export default function Sessions({ onSelectSession }) {
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');

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
    {
      session_id: 'c3d4e5f6-0011-2233-4455-667788990011',
      agent_name: 'API Route Validator',
      task: 'Executing endpoint verification tests across recovery and trace endpoints',
      status: 'completed',
      total_steps: 24,
      duration: '3m 10s',
    },
    {
      session_id: 'd4e5f6a7-1122-3344-5566-778899001122',
      agent_name: 'SQL Migration Agent',
      task: 'Applying schema migrations and verifying table indexes across session database',
      status: 'failed',
      total_steps: 5,
      duration: '18s',
    },
  ]);

  const filteredSessions = sessions.filter(s => {
    const matchesSearch = s.agent_name.toLowerCase().includes(search.toLowerCase()) ||
                          s.task.toLowerCase().includes(search.toLowerCase()) ||
                          s.session_id.toLowerCase().includes(search.toLowerCase());
    const matchesFilter = filterStatus === 'all' || s.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-[#F1F5F9] font-mono flex items-center gap-2">
          <Layers className="w-5 h-5 text-[#6366F1]" />
          AGENT SESSIONS
        </h2>
        <p className="text-xs text-[#94A3B8] mt-1">
          Inspect trace history, context filtering decisions, and checkpoint recovery records.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-[#12121A] border border-[#1E1E2E] p-4 rounded-xl">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-[#94A3B8] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by agent, task, or ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-[#0A0A0F] border border-[#1E1E2E] rounded-lg pl-9 pr-4 py-2 text-xs font-mono text-[#F1F5F9] focus:outline-none focus:border-[#6366F1] transition-colors"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto font-mono text-xs">
          <Filter className="w-4 h-4 text-[#94A3B8]" />
          <span className="text-[#94A3B8]">Status:</span>
          {['all', 'running', 'completed', 'recovered', 'failed'].map((status) => (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`px-3 py-1.5 rounded-lg border capitalize transition-colors ${
                filterStatus === status
                  ? 'bg-[#6366F1]/10 text-[#6366F1] border-[#6366F1]/30 font-semibold'
                  : 'bg-[#0A0A0F] text-[#94A3B8] border-[#1E1E2E] hover:text-[#F1F5F9]'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Grid of Agent Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredSessions.map((agent) => (
          <AgentCard
            key={agent.session_id}
            agent={agent}
            onClick={(id) => onSelectSession && onSelectSession(id)}
          />
        ))}
      </div>
    </div>
  );
}
