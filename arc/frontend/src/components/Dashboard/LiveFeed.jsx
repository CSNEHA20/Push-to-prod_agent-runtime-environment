import React from 'react';
import useWebSocket from '../../hooks/useWebSocket';
import { 
  Activity, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  RefreshCw, 
  Wifi, 
  WifiOff, 
  Zap, 
  ShieldAlert,
  Clock
} from 'lucide-react';

/**
 * LiveFeed component
 * Subscribes to session WebSocket stream and renders styled real-time event logs.
 * Event types:
 * - step_completed: subtle gray row
 * - conflict_detected: amber highlighted row
 * - failure_detected: red highlighted row
 * - recovery_complete: green highlighted row
 * - session_complete: bold green row
 */
export default function LiveFeed({ sessionId = 'a1b2c3d4-8899-0011-2233-445566778899' }) {
  const { events, isConnected } = useWebSocket(sessionId);

  // Fallback demonstration events if WebSocket is connecting or idle
  const fallbackEvents = [
    {
      id: 'evt-5',
      event_type: 'session_complete',
      timestamp: new Date().toISOString(),
      message: 'Agent session completed successfully following state recovery.',
      details: { total_steps: 5, status: 'SUCCESS' }
    },
    {
      id: 'evt-4',
      event_type: 'recovery_complete',
      timestamp: new Date(Date.now() - 10000).toISOString(),
      message: 'Recovery Engine restored checkpoint Step #2 and verified safe execution.',
      details: { recovered_step: 4, rollback_target: 2 }
    },
    {
      id: 'evt-3',
      event_type: 'failure_detected',
      timestamp: new Date(Date.now() - 60000).toISOString(),
      message: 'Step #3 tool execution failed with connection pool parameter exception.',
      details: { step_number: 3, error: 'DatabaseError: Connection pool reset failure' }
    },
    {
      id: 'evt-2',
      event_type: 'conflict_detected',
      timestamp: new Date(Date.now() - 65000).toISOString(),
      message: 'Context Firewall intercepted 1 critical parameter contradiction in raw sources.',
      details: { conflict_id: 'conf-1', severity: 'critical' }
    },
    {
      id: 'evt-1',
      event_type: 'step_completed',
      timestamp: new Date(Date.now() - 110000).toISOString(),
      message: 'Step #1 tool call search_codebase completed with score 0.94.',
      details: { step_number: 1, tool: 'search_codebase' }
    }
  ];

  const displayEvents = events && events.length > 0 ? events : fallbackEvents;

  const renderEventRow = (evt, idx) => {
    const type = evt.event_type || evt.type;
    const timeStr = evt.timestamp 
      ? new Date(evt.timestamp).toLocaleTimeString() 
      : new Date().toLocaleTimeString();

    switch (type) {
      case 'session_complete':
        return (
          <div
            key={evt.id || idx}
            className="p-3.5 rounded-lg bg-emerald-500/20 border-2 border-emerald-500/50 text-emerald-300 font-bold flex items-center justify-between shadow-md"
          >
            <div className="flex items-center gap-2.5">
              <Zap className="w-5 h-5 text-emerald-400 animate-pulse" />
              <span>{evt.message || 'Session completed successfully.'}</span>
            </div>
            <span className="text-[10px] font-mono opacity-80">{timeStr}</span>
          </div>
        );

      case 'recovery_complete':
        return (
          <div
            key={evt.id || idx}
            className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold flex items-center justify-between"
          >
            <div className="flex items-center gap-2.5">
              <RefreshCw className="w-4 h-4 text-emerald-400" />
              <span>{evt.message || 'Recovery completed successfully.'}</span>
            </div>
            <span className="text-[10px] font-mono text-emerald-400/70">{timeStr}</span>
          </div>
        );

      case 'failure_detected':
        return (
          <div
            key={evt.id || idx}
            className="p-3 rounded-lg bg-red-500/15 border border-red-500/40 text-red-300 font-semibold flex items-center justify-between"
          >
            <div className="flex items-center gap-2.5">
              <XCircle className="w-4 h-4 text-red-400" />
              <span>{evt.message || 'Execution failure intercepted.'}</span>
            </div>
            <span className="text-[10px] font-mono text-red-400/70">{timeStr}</span>
          </div>
        );

      case 'conflict_detected':
        return (
          <div
            key={evt.id || idx}
            className="p-3 rounded-lg bg-amber-500/15 border border-amber-500/40 text-amber-300 font-semibold flex items-center justify-between"
          >
            <div className="flex items-center gap-2.5">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              <span>{evt.message || 'Semantic conflict detected.'}</span>
            </div>
            <span className="text-[10px] font-mono text-amber-400/70">{timeStr}</span>
          </div>
        );

      case 'step_completed':
      default:
        return (
          <div
            key={evt.id || idx}
            className="p-2.5 rounded-lg bg-arc-bg/80 border border-arc-outline/60 text-arc-textSecondary hover:text-arc-textPrimary flex items-center justify-between text-xs transition-colors"
          >
            <div className="flex items-center gap-2.5">
              <Activity className="w-3.5 h-3.5 text-arc-primary" />
              <span>{evt.message || `Step executed successfully.`}</span>
            </div>
            <span className="text-[10px] font-mono text-arc-textSecondary/70">{timeStr}</span>
          </div>
        );
    }
  };

  return (
    <div className="bg-arc-surface border border-arc-outline rounded-xl p-5 font-mono space-y-4 shadow-sm">
      <div className="flex items-center justify-between border-b border-arc-outline pb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-arc-primary" />
          <h3 className="text-sm font-bold text-arc-textPrimary uppercase tracking-wider">
            Real-Time Telemetry Live Feed
          </h3>
        </div>

        {/* WebSocket Connection Indicator */}
        <div className="flex items-center gap-2">
          {isConnected ? (
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
              <Wifi className="w-3 h-3 text-emerald-400 animate-pulse" />
              WS CONNECTED
            </span>
          ) : (
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 flex items-center gap-1">
              <WifiOff className="w-3 h-3 text-amber-400" />
              RECONNECTING
            </span>
          )}
        </div>
      </div>

      {/* Events Stream List */}
      <div className="space-y-2 max-h-[350px] overflow-y-auto pr-1">
        {displayEvents.map((evt, idx) => renderEventRow(evt, idx))}
      </div>
    </div>
  );
}
