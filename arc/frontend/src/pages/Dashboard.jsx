import React, { useState, useEffect } from 'react';
import { Activity, Radio, RefreshCw, CheckCircle2, ShieldAlert, ArrowUpRight, Cpu } from 'lucide-react';
import AgentCard from '../components/Dashboard/AgentCard';

export default function Dashboard({ onSelectSession }) {
  const [stats, setStats] = useState({
    totalSessions: 142,
    activeSessions: 4,
    successRate: '98.4%',
    avgRecoveryTime: '340ms',
  });

  const [agents, setAgents] = useState([
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

  const [liveFeed, setLiveFeed] = useState([
    { id: 1, session_name: 'Claude Code Synthesizer', status: 'running', step: 12, time_ago: '2s ago' },
    { id: 2, session_name: 'Context Firewall Evaluator', status: 'recovered', step: 8, time_ago: '45s ago' },
    { id: 3, session_name: 'API Route Validator', status: 'completed', step: 24, time_ago: '3m ago' },
    { id: 4, session_name: 'SQL Migration Agent', status: 'failed', step: 5, time_ago: '8m ago' },
    { id: 5, session_name: 'Flight Recorder Streamer', status: 'completed', step: 19, time_ago: '14m ago' },
  ]);

  useEffect(() => {
    // Fetch live sessions from API if available
    const fetchDashboardData = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/sessions');
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            setAgents(data);
            setStats(prev => ({
              ...prev,
              totalSessions: data.length,
              activeSessions: data.filter(s => s.status === 'running').length,
            }));
          }
        }
      } catch (err) {
        // Fallback to sample data if backend not reachable
      }
    };

    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 5000);
    return () => clearInterval(interval);
  }, []);

  const renderFeedBadge = (status) => {
    switch (status) {
      case 'running':
        return <span className="text-[#6366F1] font-mono text-xs font-semibold">● RUNNING</span>;
      case 'completed':
        return <span className="text-[#10B981] font-mono text-xs font-semibold">✓ COMPLETED</span>;
      case 'failed':
        return <span className="text-[#EF4444] font-mono text-xs font-semibold">✕ FAILED</span>;
      case 'recovered':
        return <span className="text-[#F59E0B] font-mono text-xs font-semibold">↺ RECOVERED</span>;
      default:
        return <span className="text-[#94A3B8] font-mono text-xs">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Title Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-[#F1F5F9] font-mono flex items-center gap-2">
            <Cpu className="w-5 h-5 text-[#6366F1]" />
            AGENT RUNTIME DASHBOARD
          </h2>
          <p className="text-xs text-[#94A3B8] mt-1">
            Real-time overview of agent execution traces, firewall logs, and recovery checkpoints.
          </p>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono text-[#94A3B8]">
          <span className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse"></span>
          <span>Engine Status: Active</span>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Sessions */}
        <div className="bg-[#12121A] border border-[#1E1E2E] rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-[#94A3B8] text-xs font-mono mb-2">
            <span>TOTAL SESSIONS</span>
            <Activity className="w-4 h-4 text-[#6366F1]" />
          </div>
          <div className="text-2xl font-bold text-[#F1F5F9] font-mono">{stats.totalSessions}</div>
          <p className="text-xs text-[#94A3B8] mt-2 font-mono flex items-center gap-1">
            <span className="text-[#10B981]">+12.4%</span> vs last hour
          </p>
        </div>

        {/* Active Sessions */}
        <div className="bg-[#12121A] border border-[#1E1E2E] rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-[#94A3B8] text-xs font-mono mb-2">
            <span>ACTIVE SESSIONS</span>
            <Radio className="w-4 h-4 text-[#6366F1] animate-pulse" />
          </div>
          <div className="text-2xl font-bold text-[#6366F1] font-mono">{stats.activeSessions}</div>
          <p className="text-xs text-[#94A3B8] mt-2 font-mono">Running agent threads</p>
        </div>

        {/* Success Rate */}
        <div className="bg-[#12121A] border border-[#1E1E2E] rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-[#94A3B8] text-xs font-mono mb-2">
            <span>SUCCESS RATE</span>
            <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
          </div>
          <div className="text-2xl font-bold text-[#10B981] font-mono">{stats.successRate}</div>
          <p className="text-xs text-[#94A3B8] mt-2 font-mono">Post-recovery execution</p>
        </div>

        {/* Avg Recovery Time */}
        <div className="bg-[#12121A] border border-[#1E1E2E] rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-[#94A3B8] text-xs font-mono mb-2">
            <span>AVG RECOVERY TIME</span>
            <RefreshCw className="w-4 h-4 text-[#F59E0B]" />
          </div>
          <div className="text-2xl font-bold text-[#F59E0B] font-mono">{stats.avgRecoveryTime}</div>
          <p className="text-xs text-[#94A3B8] mt-2 font-mono">Checkpoint rollback latency</p>
        </div>
      </div>

      {/* Main Content Grid: Active Agents + Live Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Agents Grid (2 columns on large screen) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[#F1F5F9] font-mono uppercase tracking-wider">
              Agent Execution Sessions ({agents.length})
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {agents.map((agent) => (
              <AgentCard
                key={agent.session_id}
                agent={agent}
                onClick={(id) => onSelectSession && onSelectSession(id)}
              />
            ))}
          </div>
        </div>

        {/* Live Feed Section */}
        <div className="bg-[#12121A] border border-[#1E1E2E] rounded-xl p-5 flex flex-col shadow-lg">
          <div className="flex items-center justify-between pb-4 border-b border-[#1E1E2E]">
            <h3 className="text-sm font-semibold text-[#F1F5F9] font-mono uppercase tracking-wider flex items-center gap-2">
              <Radio className="w-4 h-4 text-[#6366F1] animate-pulse" />
              Live Activity Feed
            </h3>
            <span className="text-xs font-mono text-[#94A3B8]">Real-time</span>
          </div>

          <div className="divide-y divide-[#1E1E2E]/60 overflow-y-auto max-h-[420px] mt-2 font-mono">
            {liveFeed.map((item) => (
              <div
                key={item.id}
                onClick={() => onSelectSession && onSelectSession(item.id)}
                className="py-3 px-2 hover:bg-[#1E1E2E]/40 rounded-lg transition-colors cursor-pointer group flex items-center justify-between"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    {renderFeedBadge(item.status)}
                    <span className="text-xs text-[#F1F5F9] font-medium group-hover:text-[#6366F1] transition-colors">
                      {item.session_name}
                    </span>
                  </div>
                  <div className="text-[11px] text-[#94A3B8]">
                    Step <strong className="text-slate-200">{item.step}</strong> executed
                  </div>
                </div>

                <div className="text-right">
                  <span className="text-[11px] text-[#94A3B8]">{item.time_ago}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
