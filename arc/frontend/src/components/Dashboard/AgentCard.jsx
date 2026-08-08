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
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-arc-primary/10 text-arc-primary border border-arc-primary/20">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-arc-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-arc-primary"></span>
            </span>
            running
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-arc-tertiary/10 text-arc-tertiary border border-arc-tertiary/20">
            <CheckCircle2 className="w-3.5 h-3.5" />
            completed
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-arc-error/10 text-arc-error border border-arc-error/20">
            <AlertOctagon className="w-3.5 h-3.5" />
            failed
          </span>
        );
      case 'recovered':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-arc-secondary/10 text-arc-secondary border border-arc-secondary/20">
            <RefreshCw className="w-3.5 h-3.5" />
            recovered
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-arc-surface text-arc-textSecondary border border-arc-outline">
            {status}
          </span>
        );
    }
  };

  return (
    <div
      onClick={() => onClick && onClick(session_id)}
      className="bg-arc-surface border border-arc-outline hover:border-arc-primary/50 rounded-xl p-5 transition-all cursor-pointer group shadow-lg shadow-black/20 hover:shadow-arc-primary/5"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-arc-outline group-hover:bg-arc-primary/10 group-hover:text-arc-primary flex items-center justify-center text-arc-textSecondary font-mono text-sm font-semibold transition-colors">
            {agent_name.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <h3 className="font-semibold text-arc-textPrimary text-base group-hover:text-arc-primary transition-colors leading-tight">
              {agent_name}
            </h3>
            <p className="text-xs font-mono text-arc-textSecondary mt-0.5">
              ID: {session_id ? String(session_id).slice(0, 8) : '—'}
            </p>
          </div>
        </div>
        {renderStatusBadge()}
      </div>

      <p className="text-sm text-arc-textSecondary line-clamp-2 mb-4 h-10 leading-relaxed">
        {task}
      </p>

      <div className="flex items-center justify-between text-xs text-arc-textSecondary pt-3 border-t border-arc-outline/60 font-mono">
        <div className="flex items-center space-x-1.5">
          <Layers className="w-3.5 h-3.5 text-arc-textSecondary" />
          <span>Steps: <strong className="text-arc-textPrimary font-medium">{total_steps}</strong></span>
        </div>
        <div className="flex items-center space-x-1.5">
          <Clock className="w-3.5 h-3.5 text-arc-textSecondary" />
          <span>Duration: <strong className="text-arc-textPrimary font-medium">{duration}</strong></span>
        </div>
      </div>
    </div>
  );
}
