import React from 'react';
import { Activity, CheckCircle2, AlertOctagon, RefreshCw, Clock, Layers } from 'lucide-react';

export default function AgentCard({ agent, onClick }) {
  const {
    session_id,
    agent_name = "Claude Agent",
    task = "Executing agent workflow",
    status = "running",
    total_steps = 0,
    started_at,
    duration = "0s",
  } = agent;

  const renderStatusBadge = () => {
    switch (status.toLowerCase()) {
      case 'running':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-[#6366F1]/10 text-[#6366F1] border border-[#6366F1]/20">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#6366F1] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#6366F1]"></span>
            </span>
            running
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-[#10B981]/10 text-[#10B981] border border-[#10B981]/20">
            <CheckCircle2 className="w-3.5 h-3.5" />
            completed
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-[#EF4444]/10 text-[#EF4444] border border-[#EF4444]/20">
            <AlertOctagon className="w-3.5 h-3.5" />
            failed
          </span>
        );
      case 'recovered':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-[#F59E0B]/10 text-[#F59E0B] border border-[#F59E0B]/20">
            <RefreshCw className="w-3.5 h-3.5" />
            recovered
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
            {status}
          </span>
        );
    }
  };

  return (
    <div
      onClick={() => onClick && onClick(session_id)}
      className="bg-[#12121A] border border-[#1E1E2E] hover:border-[#6366F1]/50 rounded-xl p-5 transition-all cursor-pointer group shadow-lg shadow-black/20 hover:shadow-[#6366F1]/5"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-[#1E1E2E] group-hover:bg-[#6366F1]/10 group-hover:text-[#6366F1] flex items-center justify-center text-slate-300 font-mono text-sm font-semibold transition-colors">
            {agent_name.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <h3 className="font-semibold text-[#F1F5F9] text-base group-hover:text-[#6366F1] transition-colors leading-tight">
              {agent_name}
            </h3>
            <p className="text-xs font-mono text-[#94A3B8] mt-0.5">
              ID: {session_id ? String(session_id).slice(0, 8) : '—'}
            </p>
          </div>
        </div>
        {renderStatusBadge()}
      </div>

      <p className="text-sm text-[#94A3B8] line-clamp-2 mb-4 h-10 leading-relaxed">
        {task}
      </p>

      <div className="flex items-center justify-between text-xs text-[#94A3B8] pt-3 border-t border-[#1E1E2E]/60 font-mono">
        <div className="flex items-center space-x-1.5">
          <Layers className="w-3.5 h-3.5 text-slate-500" />
          <span>Steps: <strong className="text-[#F1F5F9] font-medium">{total_steps}</strong></span>
        </div>
        <div className="flex items-center space-x-1.5">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          <span>Duration: <strong className="text-[#F1F5F9] font-medium">{duration}</strong></span>
        </div>
      </div>
    </div>
  );
}
