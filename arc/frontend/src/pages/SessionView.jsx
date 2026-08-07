import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  ShieldAlert, 
  RefreshCw, 
  ArrowLeft, 
  Clock, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  GitCommit, 
  FileText,
  Shield,
  Layers,
  Database,
  Cpu,
  Check
} from 'lucide-react';
import TraceTimeline from '../components/FlightRecorder/TraceTimeline';
import ReplayControls from '../components/FlightRecorder/ReplayControls';

export default function SessionView({ sessionId = 'a1b2c3d4-8899-0011-2233-445566778899', onBack }) {
  const [activeTab, setActiveTab] = useState('flight_recorder'); // 'flight_recorder' | 'context_firewall' | 'recovery_engine'
  const [session, setSession] = useState(null);
  const [traceSteps, setTraceSteps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Replay state
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const timerRef = useRef(null);

  // Fetch session & trace data
  useEffect(() => {
    let isMounted = true;

    async function fetchData() {
      setLoading(true);
      setError(null);

      try {
        const [sessionRes, traceRes] = await Promise.all([
          fetch(`http://localhost:8000/api/sessions/${sessionId}`),
          fetch(`http://localhost:8000/api/sessions/${sessionId}/trace`)
        ]);

        if (sessionRes.ok && traceRes.ok) {
          const sessionData = await sessionRes.json();
          const traceData = await traceRes.json();

          if (isMounted) {
            setSession(sessionData);
            setTraceSteps(traceData);
            setLoading(false);
            return;
          }
        }
      } catch (err) {
        console.warn('Backend API unavailable, using fallback demonstration data.', err);
      }

      // Fallback mock session data if API not available or returns error
      if (isMounted) {
        setSession({
          session_id: sessionId,
          agent_name: 'Claude Code Synthesizer',
          task: 'Refactoring async session handler & optimizing SQL database queries for PostgreSQL',
          status: 'recovered',
          started_at: new Date(Date.now() - 120000).toISOString(),
          ended_at: new Date().toISOString(),
          total_steps: 5,
          failed_at_step: 3,
          recovered: true
        });

        setTraceSteps([
          {
            step_id: 'step-1',
            session_id: sessionId,
            step_number: 1,
            step_type: 'tool_call',
            timestamp: new Date(Date.now() - 110000).toISOString(),
            duration_ms: 450,
            tool_name: 'search_codebase',
            tool_input: { query: 'async_session_handler', path: 'src/db/' },
            tool_output: { matches_found: 3, file: 'src/db/connection.py' },
            confidence_score: 0.94,
            reasoning_summary: 'Locating the legacy session handler implementation in backend connection modules.',
            status: 'completed',
            was_recovered: false,
            input_data: { query: 'async_session_handler', limit: 10 },
            output_data: { matches: ['src/db/connection.py', 'src/db/session.py'] }
          },
          {
            step_id: 'step-2',
            session_id: sessionId,
            step_number: 2,
            step_type: 'llm_call',
            timestamp: new Date(Date.now() - 90000).toISOString(),
            duration_ms: 1820,
            confidence_score: 0.88,
            reasoning_summary: 'Analyzing PostgreSQL pool connection parameters and generating optimal pooled async config.',
            status: 'completed',
            was_recovered: false,
            input_data: { model: 'claude-sonnet-4-6', prompt: 'Refactor ConnectionPool for max 20 connections' },
            output_data: { proposed_diff: 'async_engine = create_async_engine(DATABASE_URL, pool_size=20)' }
          },
          {
            step_id: 'step-3',
            session_id: sessionId,
            step_number: 3,
            step_type: 'tool_call',
            timestamp: new Date(Date.now() - 60000).toISOString(),
            duration_ms: 1200,
            tool_name: 'execute_sql',
            confidence_score: 0.35,
            reasoning_summary: 'Executing schema migration script. Triggered invalid syntax error during connection pool reset.',
            status: 'failed',
            error: 'DatabaseError: Connection refused (invalid pool parameter max_overflow=NaN)',
            was_recovered: false,
            input_data: { sql: 'ALTER SYSTEM SET max_connections = NaN;' },
            output_data: { error: 'SyntaxError near NaN' }
          },
          {
            step_id: 'step-4',
            session_id: sessionId,
            step_number: 4,
            step_type: 'decision',
            timestamp: new Date(Date.now() - 35000).toISOString(),
            duration_ms: 650,
            confidence_score: 0.76,
            reasoning_summary: 'Recovery Engine intervention: Restoring previous safe state checkpoint #2 and applying verified patch.',
            status: 'completed',
            was_recovered: true,
            input_data: { action: 'rollback_checkpoint', checkpoint_id: 'chk-step-2' },
            output_data: { state_restored: true, target_step: 2 }
          },
          {
            step_id: 'step-5',
            session_id: sessionId,
            step_number: 5,
            step_type: 'tool_call',
            timestamp: new Date(Date.now() - 10000).toISOString(),
            duration_ms: 890,
            tool_name: 'apply_patch',
            confidence_score: 0.96,
            reasoning_summary: 'Applying safe connection pool patch (max_overflow=10). All test suites passing.',
            status: 'completed',
            was_recovered: true,
            input_data: { file: 'src/db/connection.py', max_overflow: 10 },
            output_data: { status: 'SUCCESS', tests_passed: 14 }
          }
        ]);
        setLoading(false);
      }
    }

    fetchData();

    return () => {
      isMounted = false;
    };
  }, [sessionId]);

  // Replay playback interval timer
  useEffect(() => {
    if (isPlaying && traceSteps.length > 0) {
      const intervalTime = 1500 / playbackSpeed;
      timerRef.current = setInterval(() => {
        setCurrentStepIndex((prev) => {
          if (prev >= traceSteps.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, intervalTime);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, playbackSpeed, traceSteps.length]);

  const handlePlayToggle = () => {
    if (!isPlaying && currentStepIndex >= traceSteps.length - 1) {
      setCurrentStepIndex(0);
    }
    setIsPlaying(!isPlaying);
  };

  const getStatusBadge = (status, isRecovered) => {
    if (isRecovered || status === 'recovered') {
      return (
        <span className="px-2.5 py-1 rounded-full text-xs font-mono font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30 flex items-center gap-1.5">
          <RefreshCw className="w-3.5 h-3.5" />
          Recovered
        </span>
      );
    }
    if (status === 'failed' || status === 'error') {
      return (
        <span className="px-2.5 py-1 rounded-full text-xs font-mono font-semibold bg-red-500/15 text-red-400 border border-red-500/30 flex items-center gap-1.5">
          <XCircle className="w-3.5 h-3.5" />
          Failed
        </span>
      );
    }
    if (status === 'running') {
      return (
        <span className="px-2.5 py-1 rounded-full text-xs font-mono font-semibold bg-arc-primary/15 text-arc-primary border border-arc-primary/30 flex items-center gap-1.5 animate-pulse">
          <Activity className="w-3.5 h-3.5" />
          Running
        </span>
      );
    }
    return (
      <span className="px-2.5 py-1 rounded-full text-xs font-mono font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
        <CheckCircle2 className="w-3.5 h-3.5" />
        Completed
      </span>
    );
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center p-12 font-mono text-arc-textSecondary">
        <div className="flex flex-col items-center gap-3">
          <Activity className="w-8 h-8 text-arc-primary animate-spin" />
          <span>Loading session trace data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full space-y-6">
      {/* Top Header Card */}
      <div className="bg-arc-surface border border-arc-outline rounded-xl p-5 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            {onBack && (
              <button
                onClick={onBack}
                className="mt-1 p-2 rounded-lg bg-arc-bg border border-arc-outline hover:border-arc-primary text-arc-textSecondary hover:text-arc-textPrimary transition-colors"
                title="Back to Sessions"
              >
                <ArrowLeft className="w-4 h-4" />
              </button>
            )}
            <div>
              <div className="flex items-center gap-3 flex-wrap">
                <h1 className="text-lg font-bold font-mono text-arc-textPrimary tracking-tight">
                  {session?.agent_name || 'Agent Session'}
                </h1>
                {getStatusBadge(session?.status, session?.recovered)}
              </div>
              <p className="text-xs font-mono text-arc-textSecondary mt-1">
                {session?.task}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 font-mono text-xs text-arc-textSecondary border-t md:border-t-0 pt-3 md:pt-0 border-arc-outline">
            <div className="bg-arc-bg border border-arc-outline px-3 py-1.5 rounded-lg">
              Session ID: <strong className="text-arc-textPrimary">{sessionId.slice(0, 8)}...</strong>
            </div>
            <div className="bg-arc-bg border border-arc-outline px-3 py-1.5 rounded-lg">
              Steps: <strong className="text-arc-primary">{traceSteps.length}</strong>
            </div>
          </div>
        </div>

        {/* Tab Navigation Header */}
        <div className="flex items-center space-x-2 mt-6 pt-4 border-t border-arc-outline font-mono text-xs">
          <button
            onClick={() => setActiveTab('flight_recorder')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg border transition-all font-semibold ${
              activeTab === 'flight_recorder'
                ? 'bg-arc-primary/10 text-arc-primary border-arc-primary/40 shadow-sm'
                : 'bg-arc-bg text-arc-textSecondary border-arc-outline hover:text-arc-textPrimary hover:bg-arc-outline/30'
            }`}
          >
            <Activity className="w-4 h-4 text-arc-primary" />
            <span>Flight Recorder</span>
          </button>

          <button
            onClick={() => setActiveTab('context_firewall')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg border transition-all font-semibold ${
              activeTab === 'context_firewall'
                ? 'bg-arc-secondary/10 text-arc-secondary border-arc-secondary/40 shadow-sm'
                : 'bg-arc-bg text-arc-textSecondary border-arc-outline hover:text-arc-textPrimary hover:bg-arc-outline/30'
            }`}
          >
            <Shield className="w-4 h-4 text-arc-secondary" />
            <span>Context Firewall</span>
          </button>

          <button
            onClick={() => setActiveTab('recovery_engine')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg border transition-all font-semibold ${
              activeTab === 'recovery_engine'
                ? 'bg-arc-tertiary/10 text-arc-tertiary border-arc-tertiary/40 shadow-sm'
                : 'bg-arc-bg text-arc-textSecondary border-arc-outline hover:text-arc-textPrimary hover:bg-arc-outline/30'
            }`}
          >
            <RefreshCw className="w-4 h-4 text-arc-tertiary" />
            <span>Recovery Engine</span>
          </button>
        </div>
      </div>

      {/* Main Tab Content */}
      <div className="flex-1 min-h-0">
        {/* Tab 1: Flight Recorder */}
        {activeTab === 'flight_recorder' && (
          <div className="flex flex-col space-y-4 h-full">
            {/* Replay Controls bar */}
            <ReplayControls
              isPlaying={isPlaying}
              onPlayToggle={handlePlayToggle}
              currentStepIndex={currentStepIndex}
              totalSteps={traceSteps.length}
              onStepChange={(idx) => {
                setCurrentStepIndex(idx);
                setIsPlaying(false);
              }}
              playbackSpeed={playbackSpeed}
              onSpeedChange={(speed) => setPlaybackSpeed(speed)}
            />

            {/* Trace Timeline Container */}
            <div className="flex-1 bg-arc-surface border border-arc-outline rounded-xl p-4 overflow-y-auto shadow-inner">
              <div className="flex items-center justify-between px-2 pb-3 mb-2 border-b border-arc-outline/50 font-mono text-xs">
                <span className="text-arc-textSecondary font-semibold uppercase tracking-wider">
                  Visual Debugger Step Execution Replay
                </span>
                <span className="text-arc-primary font-bold">
                  Step {currentStepIndex + 1} of {traceSteps.length} Selected
                </span>
              </div>

              <TraceTimeline
                steps={traceSteps}
                currentStepIndex={currentStepIndex}
                onSelectStep={(idx) => {
                  setCurrentStepIndex(idx);
                  setIsPlaying(false);
                }}
              />
            </div>
          </div>
        )}

        {/* Tab 2: Context Firewall */}
        {activeTab === 'context_firewall' && (
          <div className="bg-arc-surface border border-arc-outline rounded-xl p-6 font-mono space-y-6">
            <div className="flex items-center justify-between border-b border-arc-outline pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-arc-secondary/10 rounded-lg border border-arc-secondary/20 text-arc-secondary">
                  <ShieldAlert className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-arc-textPrimary">Context Firewall Analysis</h2>
                  <p className="text-xs text-arc-textSecondary mt-0.5">
                    Real-time prompt evaluation, semantic conflict protection & source provenance tracking.
                  </p>
                </div>
              </div>
              <span className="px-3 py-1 bg-arc-tertiary/10 border border-arc-tertiary/20 text-arc-tertiary rounded-full text-xs font-bold">
                0 Critical Contradictions Active
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className="bg-arc-bg border border-arc-outline p-4 rounded-lg">
                <span className="text-arc-textSecondary block mb-1">Context Chunks Evaluated</span>
                <span className="text-xl font-bold text-arc-textPrimary">24 Chunks</span>
              </div>
              <div className="bg-arc-bg border border-arc-outline p-4 rounded-lg">
                <span className="text-arc-textSecondary block mb-1">Passed Firewall</span>
                <span className="text-xl font-bold text-emerald-400">22 (91.6%)</span>
              </div>
              <div className="bg-arc-bg border border-arc-outline p-4 rounded-lg">
                <span className="text-arc-textSecondary block mb-1">Filtered / Rejected</span>
                <span className="text-xl font-bold text-amber-400">2 Chunks</span>
              </div>
            </div>

            {/* Provenance Matrix */}
            <div>
              <h3 className="text-xs font-semibold text-arc-textSecondary uppercase tracking-wider mb-3">
                Provenance Comparison Matrix for Session #{sessionId.slice(0, 6)}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="bg-arc-bg border border-arc-outline rounded-lg p-4 space-y-3">
                  <div className="flex justify-between items-center border-b border-arc-outline pb-2">
                    <span className="font-bold text-arc-textPrimary flex items-center gap-2">
                      <FileText className="w-4 h-4 text-arc-primary" /> Source: postgres_pool_spec.md
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      Score: 96%
                    </span>
                  </div>
                  <p className="text-arc-textSecondary leading-relaxed">
                    "AsyncEngine parameters must configure connection pool overflow explicitly between 5 and 20."
                  </p>
                  <div className="text-[10px] text-arc-tertiary font-semibold flex items-center gap-1">
                    <Check className="w-3 h-3" /> Passed Context Firewall
                  </div>
                </div>

                <div className="bg-arc-bg border border-amber-500/30 rounded-lg p-4 space-y-3">
                  <div className="flex justify-between items-center border-b border-arc-outline pb-2">
                    <span className="font-bold text-arc-textPrimary flex items-center gap-2">
                      <FileText className="w-4 h-4 text-amber-400" /> Source: unverified_forum_post.txt
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20">
                      Score: 32%
                    </span>
                  </div>
                  <p className="text-arc-textSecondary leading-relaxed">
                    "To disable connections limits, pass max_overflow=NaN in query parameter."
                  </p>
                  <div className="text-[10px] text-amber-400 font-semibold flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" /> Filtered Out: High Hallucination Risk
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Recovery Engine */}
        {activeTab === 'recovery_engine' && (
          <div className="bg-arc-surface border border-arc-outline rounded-xl p-6 font-mono space-y-6">
            <div className="flex items-center justify-between border-b border-arc-outline pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-arc-tertiary/10 rounded-lg border border-arc-tertiary/20 text-arc-tertiary">
                  <RefreshCw className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-arc-textPrimary">Recovery Engine Checkpoint Status</h2>
                  <p className="text-xs text-arc-textSecondary mt-0.5">
                    Automated failure detection, state rollback & deterministic recovery execution.
                  </p>
                </div>
              </div>
              <span className="px-3 py-1 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-full text-xs font-bold flex items-center gap-1.5">
                <RefreshCw className="w-3.5 h-3.5" />
                Session Recovered at Step #4
              </span>
            </div>

            {/* Checkpoint Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
              <div className="bg-arc-bg border border-arc-outline p-4 rounded-lg">
                <span className="text-arc-textSecondary block mb-1">Total Checkpoints</span>
                <span className="text-xl font-bold text-arc-textPrimary">5 Checkpoints</span>
              </div>
              <div className="bg-arc-bg border border-arc-outline p-4 rounded-lg">
                <span className="text-arc-textSecondary block mb-1">Valid Checkpoints</span>
                <span className="text-xl font-bold text-emerald-400">5 Valid (100%)</span>
              </div>
              <div className="bg-arc-bg border border-arc-outline p-4 rounded-lg">
                <span className="text-arc-textSecondary block mb-1">Failures Intercepted</span>
                <span className="text-xl font-bold text-red-400">1 Failure</span>
              </div>
              <div className="bg-arc-bg border border-arc-outline p-4 rounded-lg">
                <span className="text-arc-textSecondary block mb-1">Recovery Result</span>
                <span className="text-xl font-bold text-amber-400">SUCCESS</span>
              </div>
            </div>

            {/* Recovery Timeline / Diff */}
            <div className="border border-arc-outline rounded-lg bg-arc-bg p-4 space-y-4">
              <h3 className="text-xs font-semibold text-arc-textSecondary uppercase tracking-wider flex items-center gap-2">
                <GitCommit className="w-4 h-4 text-arc-tertiary" />
                Rollback State & Diff Execution
              </h3>

              <div className="p-3 bg-arc-surface border border-arc-outline rounded text-xs space-y-2">
                <div className="flex items-center justify-between text-arc-textSecondary">
                  <span>Target Restored Checkpoint: <strong className="text-arc-primary">chk_step_02</strong></span>
                  <span>Validation Score: <strong className="text-emerald-400">0.98</strong></span>
                </div>
                <div className="p-3 bg-[#131316] rounded border border-arc-outline font-mono text-[11px] space-y-1">
                  <div className="text-red-400">- ConnectionPool(max_connections=NaN, overflow=False)</div>
                  <div className="text-emerald-400">+ ConnectionPool(max_connections=20, max_overflow=10)</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
