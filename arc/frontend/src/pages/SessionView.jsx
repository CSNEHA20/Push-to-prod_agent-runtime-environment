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
import ContextGraph from '../components/ContextFirewall/ContextGraph';
import ConflictAlert from '../components/ContextFirewall/ConflictAlert';
import ProvenanceTag from '../components/ContextFirewall/ProvenanceTag';
import CheckpointList from '../components/RecoveryEngine/CheckpointList';
import RecoveryStatus from '../components/RecoveryEngine/RecoveryStatus';
import LiveFeed from '../components/Dashboard/LiveFeed';

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
          <div className="space-y-6 font-mono">
            {/* Context Firewall Header */}
            <div className="bg-arc-surface border border-arc-outline rounded-xl p-6 space-y-4 shadow-sm">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-arc-outline pb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-arc-secondary/15 rounded-xl border border-arc-secondary/30 text-arc-secondary shadow-sm">
                    <ShieldAlert className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-arc-textPrimary">Context Firewall Engine Analysis</h2>
                    <p className="text-xs text-arc-textSecondary mt-0.5">
                      Real-time prompt evaluation, semantic conflict protection & source provenance tracking.
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 bg-red-500/15 border border-red-500/30 text-red-400 rounded-full text-xs font-bold flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    2 Conflicts Intercepted
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                <div className="bg-arc-bg border border-arc-outline p-3.5 rounded-lg">
                  <span className="text-arc-textSecondary block mb-1">Total Sources Received</span>
                  <span className="text-xl font-bold text-arc-textPrimary">5 Sources</span>
                </div>
                <div className="bg-arc-bg border border-emerald-500/30 p-3.5 rounded-lg">
                  <span className="text-arc-textSecondary block mb-1">Passed Firewall</span>
                  <span className="text-xl font-bold text-emerald-400">3 Passed (60%)</span>
                </div>
                <div className="bg-arc-bg border border-red-500/30 p-3.5 rounded-lg">
                  <span className="text-arc-textSecondary block mb-1">Filtered / Rejected</span>
                  <span className="text-xl font-bold text-red-400">2 Rejected (40%)</span>
                </div>
                <div className="bg-arc-bg border border-arc-outline p-3.5 rounded-lg">
                  <span className="text-arc-textSecondary block mb-1">Conflicts Intercepted</span>
                  <span className="text-xl font-bold text-amber-400">2 Conflicts</span>
                </div>
              </div>
            </div>

            {/* Visual Diagram: Context Flow Graph */}
            <ContextGraph sources={[
              {
                id: 'src-1',
                name: 'postgres_pool_spec.md',
                type: 'document',
                score: 0.96,
                status: 'PASSED',
                reason: null,
                snippet: 'AsyncEngine parameters must configure connection pool overflow explicitly between 5 and 20.'
              },
              {
                id: 'src-2',
                name: 'system_architecture_v2.pdf',
                type: 'document',
                score: 0.88,
                status: 'PASSED',
                reason: null,
                snippet: 'PostgreSQL async connection pool target baseline limits set to 20 connections max.'
              },
              {
                id: 'src-3',
                name: 'user_prompt_instruction',
                type: 'user',
                score: 0.94,
                status: 'PASSED',
                reason: null,
                snippet: 'Refactor async session handler and optimize connection pool settings for PostgreSQL.'
              },
              {
                id: 'src-4',
                name: 'unverified_forum_post.txt',
                type: 'api',
                score: 0.28,
                status: 'REJECTED',
                reason: 'Low Relevance (<30%) & Hallucination Risk',
                snippet: 'To disable connection limits completely, set max_overflow=NaN in query parameter.'
              },
              {
                id: 'src-5',
                name: 'legacy_mysql_config.ini',
                type: 'api',
                score: 0.15,
                status: 'REJECTED',
                reason: 'Irrelevant Context (MySQL engine config)',
                snippet: 'max_connections = 100, wait_timeout = 28800 for MySQL 5.7 legacy instance.'
              }
            ]} />

            {/* List of Detected Conflicts */}
            <ConflictAlert conflicts={[
              {
                id: 'conf-1',
                severity: 'critical',
                type: 'Numerical',
                description: 'Severe discrepancy detected between max connection overflow spec (max 20) and unverified forum post advising NaN parameter setting.',
                resolution: 'Enforced official spec postgres_pool_spec.md (max_overflow=10). Rejected unverified forum post.',
                detected_at: new Date(Date.now() - 65000).toISOString(),
                sourceA: {
                  name: 'postgres_pool_spec.md',
                  type: 'document',
                  snippet: 'AsyncEngine parameters must configure connection pool overflow explicitly between 5 and 20.'
                },
                sourceB: {
                  name: 'unverified_forum_post.txt',
                  type: 'api',
                  snippet: 'To disable connection limits completely, set max_overflow=NaN in query parameter.'
                }
              },
              {
                id: 'conf-2',
                severity: 'medium',
                type: 'Factual',
                description: 'Database dialect mismatch: legacy MySQL configuration mixed into PostgreSQL async session refactor task.',
                resolution: 'Filtered out legacy_mysql_config.ini from prompt payload before sending to Claude.',
                detected_at: new Date(Date.now() - 70000).toISOString(),
                sourceA: {
                  name: 'system_architecture_v2.pdf',
                  type: 'document',
                  snippet: 'PostgreSQL async connection pool target baseline limits set to 20 connections max.'
                },
                sourceB: {
                  name: 'legacy_mysql_config.ini',
                  type: 'api',
                  snippet: 'max_connections = 100, wait_timeout = 28800 for MySQL 5.7 legacy instance.'
                }
              }
            ]} />

            {/* Final Context Display with Provenance Tags */}
            <div className="bg-arc-surface border border-arc-outline rounded-xl p-5 font-mono space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-arc-outline pb-3">
                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-arc-primary" />
                  <h3 className="text-sm font-bold text-arc-textPrimary uppercase tracking-wider">
                    Sanitized Context Stream (Passed To Claude)
                  </h3>
                </div>
                <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Provenance Tagged
                </span>
              </div>

              <div className="bg-arc-bg border border-arc-outline rounded-lg p-4 space-y-3">
                <div className="p-3 bg-arc-surface rounded-lg border border-arc-outline/60 space-y-2">
                  <div className="flex justify-between items-center flex-wrap gap-2">
                    <ProvenanceTag sourceName="user_prompt_instruction" confidence={0.94} type="user" />
                    <span className="text-[10px] font-mono text-arc-textSecondary">
                      Chunk #1 • Instruction
                    </span>
                  </div>
                  <p className="text-xs text-arc-textPrimary leading-relaxed font-mono bg-arc-bg/40 p-2.5 rounded border border-arc-outline/30">
                    "Refactor async session handler and optimize connection pool settings for PostgreSQL."
                  </p>
                </div>

                <div className="p-3 bg-arc-surface rounded-lg border border-arc-outline/60 space-y-2">
                  <div className="flex justify-between items-center flex-wrap gap-2">
                    <ProvenanceTag sourceName="postgres_pool_spec.md" confidence={0.96} type="document" />
                    <span className="text-[10px] font-mono text-arc-textSecondary">
                      Chunk #2 • Spec Document
                    </span>
                  </div>
                  <p className="text-xs text-arc-textPrimary leading-relaxed font-mono bg-arc-bg/40 p-2.5 rounded border border-arc-outline/30">
                    "AsyncEngine parameters must configure connection pool overflow explicitly between 5 and 20."
                  </p>
                </div>

                <div className="p-3 bg-arc-surface rounded-lg border border-arc-outline/60 space-y-2">
                  <div className="flex justify-between items-center flex-wrap gap-2">
                    <ProvenanceTag sourceName="system_architecture_v2.pdf" confidence={0.88} type="document" />
                    <span className="text-[10px] font-mono text-arc-textSecondary">
                      Chunk #3 • Architecture Doc
                    </span>
                  </div>
                  <p className="text-xs text-arc-textPrimary leading-relaxed font-mono bg-arc-bg/40 p-2.5 rounded border border-arc-outline/30">
                    "PostgreSQL async connection pool target baseline limits set to 20 connections max."
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Recovery Engine */}
        {activeTab === 'recovery_engine' && (
          <div className="space-y-6 font-mono">
            {/* Checkpoint Timeline & Rollback Jumps */}
            <CheckpointList 
              steps={traceSteps.length > 0 ? traceSteps : [
                { step_number: 1, name: 'search_codebase', status: 'completed', validation_score: 0.94, timestamp: new Date(Date.now() - 110000).toISOString(), is_checkpoint: true },
                { step_number: 2, name: 'analyze_pool_config', status: 'completed', validation_score: 0.98, timestamp: new Date(Date.now() - 90000).toISOString(), is_checkpoint: true },
                { step_number: 3, name: 'execute_sql', status: 'failed', validation_score: 0.35, timestamp: new Date(Date.now() - 60000).toISOString(), error: 'DatabaseError: Connection pool parameter max_overflow=NaN', is_checkpoint: false },
                { step_number: 4, name: 'rollback_checkpoint', status: 'recovered', validation_score: 0.76, timestamp: new Date(Date.now() - 35000).toISOString(), rollback_target_step: 2, is_checkpoint: true },
                { step_number: 5, name: 'apply_patch', status: 'completed', validation_score: 0.96, timestamp: new Date(Date.now() - 10000).toISOString(), is_checkpoint: true }
              ]} 
            />

            {/* Recovery Engine Health Summary & Failure Interception Breakdown */}
            <RecoveryStatus 
              checkpointsSaved={traceSteps.filter(s => s.status !== 'failed').length || 4}
              failuresDetected={traceSteps.filter(s => s.status === 'failed').length || 1}
              recoverySuccessRate={100}
              healthStatus={session?.recovered ? 'Healthy' : 'Degraded'}
              failures={[
                {
                  id: 'fail-1',
                  failure_type: 'DatabaseError Exception',
                  error_message: 'DatabaseError: Connection refused (invalid pool parameter max_overflow=NaN)',
                  failed_at_step: 3,
                  recovered_at_step: 4,
                  rollback_checkpoint_step: 2,
                  steps_lost: 1,
                  recovery_time_ms: 650,
                  status: 'recovered'
                }
              ]}
            />

            {/* Real-time Telemetry Live Feed Hook Integration */}
            <LiveFeed sessionId={sessionId} />

            {/* Rollback Diff & Safe Patch Execution Detail */}
            <div className="bg-arc-surface border border-arc-outline rounded-xl p-5 font-mono space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-arc-outline pb-3">
                <div className="flex items-center gap-2">
                  <GitCommit className="w-5 h-5 text-arc-tertiary" />
                  <h3 className="text-sm font-bold text-arc-textPrimary uppercase tracking-wider">
                    Automated State Rollback & Code Patch Diff
                  </h3>
                </div>
                <span className="text-xs text-emerald-400 font-semibold px-2.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                  Checkpoint #2 Restored
                </span>
              </div>

              <div className="p-4 bg-arc-bg border border-arc-outline rounded-lg space-y-3">
                <div className="flex items-center justify-between text-xs text-arc-textSecondary border-b border-arc-outline/50 pb-2">
                  <span>Target Restored State: <strong className="text-arc-primary">chk_step_02 (0.98 Validation)</strong></span>
                  <span>Patch File: <strong className="text-arc-textPrimary">src/db/connection.py</strong></span>
                </div>
                
                <div className="p-3 bg-[#131316] rounded border border-arc-outline font-mono text-xs space-y-1.5 overflow-x-auto">
                  <div className="text-arc-textSecondary text-[10px]">// Reverted invalid pool configuration & applied safe async parameters</div>
                  <div className="text-red-400 font-bold">- async_engine = create_async_engine(DATABASE_URL, max_overflow=NaN)</div>
                  <div className="text-emerald-400 font-bold">+ async_engine = create_async_engine(DATABASE_URL, pool_size=20, max_overflow=10)</div>
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
