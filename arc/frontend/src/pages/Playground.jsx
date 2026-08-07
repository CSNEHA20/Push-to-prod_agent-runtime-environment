import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Terminal, 
  Zap, 
  ShieldAlert, 
  RefreshCw, 
  CheckCircle2, 
  Activity, 
  AlertTriangle, 
  ArrowRight, 
  Sliders, 
  Flame, 
  Cpu, 
  Layers, 
  ExternalLink,
  RotateCcw
} from 'lucide-react';
import TraceTimeline from '../components/FlightRecorder/TraceTimeline';

/**
 * Pre-built Scenario definitions
 */
const SCENARIOS = [
  {
    id: 'research_company',
    name: 'Research a company',
    description: 'Generates market brief, evaluates products & financials for target enterprise.',
    defaultTask: 'Research Anthropic, find their latest funding round, key Claude products, and write an enterprise investment brief.',
    conflictCount: 0,
    hasRecovery: false
  },
  {
    id: 'analyze_document',
    name: 'Analyze a document',
    description: 'Extracts technical architecture guidelines & verifies schema compatibility.',
    defaultTask: 'Analyze system architecture PDF document and verify PostgreSQL connection pool parameters.',
    conflictCount: 0,
    hasRecovery: false
  },
  {
    id: 'conflicting_sources',
    name: 'Answer with conflicting sources',
    description: 'Triggers Context Firewall conflict detection between opposing financial records.',
    defaultTask: 'Determine Q3 revenue for Acme Corp using internal spec document ($14.2M) and public blog post ($18.5M).',
    conflictCount: 2,
    hasRecovery: false
  },
  {
    id: 'api_failure_recovery',
    name: 'Long task with API failure',
    description: 'Triggers Recovery Engine auto-rollback when step #3 encounters a runtime DatabaseError exception.',
    defaultTask: 'Refactor database connection pool, run schema migration, and apply safe fallback patch.',
    conflictCount: 1,
    hasRecovery: true
  }
];

export default function Playground({ onSelectSession }) {
  const [selectedScenario, setSelectedScenario] = useState('research_company');
  const [task, setTask] = useState(SCENARIOS[0].defaultTask);
  const [injectChaos, setInjectChaos] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  
  // Trace steps state for live reveal
  const [liveSteps, setLiveSteps] = useState([]);
  const [currentStepIdx, setCurrentStepIdx] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);
  const [summaryStats, setSummaryStats] = useState(null);

  const streamTimerRef = useRef(null);

  // Update task input when scenario changes
  const handleScenarioChange = (scenarioId) => {
    setSelectedScenario(scenarioId);
    const found = SCENARIOS.find(s => s.id === scenarioId);
    if (found) {
      setTask(found.defaultTask);
      if (scenarioId === 'api_failure_recovery') {
        setInjectChaos(true);
      }
    }
  };

  // Run Agent Execution Trigger
  const handleRunAgent = async () => {
    setIsRunning(true);
    setIsCompleted(false);
    setLiveSteps([]);
    setCurrentStepIdx(0);
    setSummaryStats(null);

    const generatedSessionId = `demo-${Date.now().toString(36)}-${Math.random().toString(36).substr(2, 5)}`;
    setSessionId(generatedSessionId);

    let apiSessionId = generatedSessionId;

    try {
      const response = await fetch('http://localhost:8000/api/playground/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task,
          scenario: selectedScenario,
          inject_chaos: injectChaos
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.session_id) {
          apiSessionId = data.session_id;
          setSessionId(apiSessionId);
        }
      }
    } catch (err) {
      console.warn('[Playground] Backend /api/playground/run unavailable, streaming client simulation.', err);
    }

    // Prepare simulated step stream based on chosen scenario & chaos toggle
    const stepsSequence = buildScenarioSteps(selectedScenario, injectChaos, task);

    // Stream steps one by one like code compilation
    let index = 0;
    streamTimerRef.current = setInterval(() => {
      if (index < stepsSequence.length) {
        const nextStep = stepsSequence[index];
        setLiveSteps((prev) => [...prev, nextStep]);
        setCurrentStepIdx(index);
        index++;
      } else {
        clearInterval(streamTimerRef.current);
        setIsRunning(false);
        setIsCompleted(true);

        // Compute summary metrics
        const total = stepsSequence.length;
        const conflicts = selectedScenario === 'conflicting_sources' || injectChaos ? (selectedScenario === 'conflicting_sources' ? 2 : 1) : 0;
        const recoveries = stepsSequence.filter(s => s.was_recovered || s.status === 'recovered').length;

        setSummaryStats({
          totalSteps: total,
          conflictsDetected: conflicts,
          recoveriesMade: recoveries,
          sessionId: apiSessionId
        });
      }
    }, 1200);
  };

  useEffect(() => {
    return () => {
      if (streamTimerRef.current) clearInterval(streamTimerRef.current);
    };
  }, []);

  return (
    <div className="space-y-6 font-mono">
      {/* Header Banner */}
      <div className="bg-arc-surface border border-arc-outline rounded-xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-600/15 text-indigo-400 border border-indigo-500/30 rounded-xl shadow-sm">
              <Terminal className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-base font-bold text-arc-textPrimary tracking-tight flex items-center gap-2">
                ARC Live Agent Playground
              </h1>
              <p className="text-xs text-arc-textSecondary mt-0.5">
                Run interactive demo agent scenarios & watch Flight Recorder, Context Firewall, and Recovery Engine work in real-time.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="px-3 py-1 bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 rounded-full font-semibold flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-indigo-400" />
              Interactive Simulation
            </span>
          </div>
        </div>
      </div>

      {/* Main 40% / 60% Split Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Panel (40% width -> 5 cols on lg) */}
        <div className="lg:col-span-5 bg-arc-surface border border-arc-outline rounded-xl p-5 space-y-5 shadow-lg">
          <div className="flex items-center justify-between border-b border-arc-outline pb-3">
            <h2 className="text-xs font-bold text-arc-textPrimary uppercase tracking-wider flex items-center gap-2">
              <Sliders className="w-4 h-4 text-indigo-400" />
              Agent Controls & Prompt Builder
            </h2>
            <span className="text-[10px] text-arc-textSecondary">Config Panel</span>
          </div>

          {/* Pre-built Scenarios Dropdown */}
          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-arc-textSecondary">
              PRE-BUILT DEMO SCENARIO
            </label>
            <select
              value={selectedScenario}
              onChange={(e) => handleScenarioChange(e.target.value)}
              disabled={isRunning}
              className="w-full bg-arc-bg border border-arc-outline rounded-lg px-3.5 py-2.5 text-xs text-arc-textPrimary focus:outline-none focus:border-indigo-500 transition-colors cursor-pointer font-mono disabled:opacity-50"
            >
              {SCENARIOS.map((sc) => (
                <option key={sc.id} value={sc.id} className="bg-arc-surface text-arc-textPrimary">
                  {sc.name}
                </option>
              ))}
            </select>
            <p className="text-[11px] text-arc-textSecondary italic pt-0.5">
              {SCENARIOS.find(s => s.id === selectedScenario)?.description}
            </p>
          </div>

          {/* Task Input Textarea */}
          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-arc-textSecondary">
              WHAT SHOULD THE AGENT DO? (TASK PROMPT)
            </label>
            <textarea
              rows={4}
              value={task}
              onChange={(e) => setTask(e.target.value)}
              disabled={isRunning}
              placeholder="Type your task instructions for the Claude agent..."
              className="w-full bg-arc-bg border border-arc-outline rounded-lg p-3.5 text-xs font-mono text-arc-textPrimary focus:outline-none focus:border-indigo-500 transition-colors resize-none disabled:opacity-50 leading-relaxed"
            />
          </div>

          {/* Inject Chaos Toggle Switch */}
          <div className="bg-arc-bg border border-arc-outline rounded-lg p-3.5 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Flame className={`w-5 h-5 ${injectChaos ? 'text-amber-400 animate-pulse' : 'text-arc-textSecondary'}`} />
              <div>
                <span className="text-xs font-bold text-arc-textPrimary block">Inject Chaos Mode</span>
                <span className="text-[10px] text-arc-textSecondary block">
                  Simulates random step runtime exception & tests auto-recovery.
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => !isRunning && setInjectChaos(!injectChaos)}
              disabled={isRunning}
              className={`w-12 h-6 rounded-full transition-colors relative p-0.5 focus:outline-none border ${
                injectChaos 
                  ? 'bg-amber-500/20 border-amber-500/50' 
                  : 'bg-arc-surface border-arc-outline'
              }`}
            >
              <div
                className={`w-4 h-4 rounded-full transition-transform duration-200 shadow-md ${
                  injectChaos 
                    ? 'translate-x-6 bg-amber-400' 
                    : 'translate-x-0 bg-arc-textSecondary'
                }`}
              />
            </button>
          </div>

          {/* Full Width Indigo Run Agent Button */}
          <button
            onClick={handleRunAgent}
            disabled={isRunning || !task.trim()}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-mono text-xs font-bold rounded-lg flex items-center justify-center space-x-2 transition-all shadow-lg shadow-indigo-600/25 disabled:opacity-50 disabled:cursor-not-allowed uppercase tracking-wider"
          >
            {isRunning ? (
              <>
                <Activity className="w-4 h-4 animate-spin text-white" />
                <span>Executing Agent Stream...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current text-white" />
                <span>Run Agent with ARC Layer</span>
              </>
            )}
          </button>
        </div>

        {/* Right Panel (60% width -> 7 cols on lg) */}
        <div className="lg:col-span-7 space-y-5">
          <div className="bg-arc-surface border border-arc-outline rounded-xl p-5 space-y-4 shadow-lg min-h-[520px] flex flex-col justify-between">
            <div className="flex items-center justify-between border-b border-arc-outline pb-3">
              <div className="flex items-center gap-2">
                <Cpu className="w-5 h-5 text-arc-primary" />
                <h3 className="text-sm font-bold text-arc-textPrimary uppercase tracking-wider">
                  Live Step Trace Execution Reveal
                </h3>
              </div>

              {isRunning ? (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 flex items-center gap-1.5 animate-pulse">
                  <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
                  STREAMING LIVE
                </span>
              ) : isCompleted ? (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  SESSION FINISHED
                </span>
              ) : (
                <span className="text-xs text-arc-textSecondary">
                  Ready to execute
                </span>
              )}
            </div>

            {/* Trace Timeline Container */}
            <div className="flex-1 bg-arc-bg border border-arc-outline rounded-lg p-4 space-y-4 overflow-y-auto max-h-[420px] shadow-inner">
              {liveSteps.length === 0 ? (
                <div className="h-64 flex flex-col items-center justify-center text-center p-6 text-arc-textSecondary text-xs space-y-3">
                  <div className="p-3 bg-arc-surface rounded-full border border-arc-outline">
                    <Play className="w-6 h-6 text-arc-primary" />
                  </div>
                  <div>
                    <span className="font-bold text-arc-textPrimary block">Playground Engine Idle</span>
                    <span className="text-[11px] block mt-1 text-arc-textSecondary max-w-sm">
                      Select a scenario on the left panel and click <strong>"RUN AGENT WITH ARC LAYER"</strong> to watch the live step execution stream.
                    </span>
                  </div>
                </div>
              ) : (
                <TraceTimeline
                  steps={liveSteps}
                  currentStepIndex={currentStepIdx}
                  onSelectStep={(idx) => setCurrentStepIdx(idx)}
                />
              )}
            </div>

            {/* Bottom Status Bar / Summary */}
            {isRunning && (
              <div className="p-3 bg-indigo-600/10 border border-indigo-500/30 rounded-lg flex items-center justify-between text-xs text-indigo-300 animate-pulse font-mono">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 animate-spin text-indigo-400" />
                  <span className="font-bold">Agent Running... Processing step #{liveSteps.length}</span>
                </div>
                <span className="text-[10px] text-indigo-400">WebSocket /ws/sessions/{sessionId?.slice(0, 8)}</span>
              </div>
            )}

            {/* Summary Card when done */}
            {isCompleted && summaryStats && (
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl space-y-3 font-mono text-xs">
                <div className="flex items-center justify-between border-b border-emerald-500/20 pb-2">
                  <div className="flex items-center gap-2 font-bold text-emerald-400">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <span>Agent Session Execution Complete!</span>
                  </div>

                  {onSelectSession && (
                    <button
                      onClick={() => onSelectSession(summaryStats.sessionId)}
                      className="px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 font-bold border border-emerald-500/40 flex items-center gap-1.5 transition-colors"
                    >
                      <span>View Full Session</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="bg-arc-surface p-2.5 rounded border border-arc-outline">
                    <span className="text-[10px] text-arc-textSecondary block">Total Steps</span>
                    <span className="text-base font-extrabold text-arc-textPrimary">{summaryStats.totalSteps}</span>
                  </div>
                  <div className="bg-arc-surface p-2.5 rounded border border-arc-outline">
                    <span className="text-[10px] text-arc-textSecondary block">Conflicts Intercepted</span>
                    <span className="text-base font-extrabold text-amber-400">{summaryStats.conflictsDetected}</span>
                  </div>
                  <div className="bg-arc-surface p-2.5 rounded border border-arc-outline">
                    <span className="text-[10px] text-arc-textSecondary block">Recoveries Made</span>
                    <span className="text-base font-extrabold text-emerald-400">{summaryStats.recoveriesMade}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Helper to build rich, realistic step objects for the selected playground scenario
 */
function buildScenarioSteps(scenarioId, injectChaos, taskPrompt) {
  if (scenarioId === 'conflicting_sources') {
    return [
      {
        step_id: 'step-1',
        step_number: 1,
        step_type: 'tool_call',
        timestamp: new Date(Date.now() - 30000).toISOString(),
        duration_ms: 380,
        tool_name: 'search_financial_records',
        confidence_score: 0.94,
        reasoning_summary: 'Retrieving enterprise Q3 revenue records from internal spec and external audit sources.',
        status: 'completed',
        input_data: { query: 'Q3 revenue Acme Corp' },
        output_data: { sources_retrieved: 2 }
      },
      {
        step_id: 'step-2',
        step_number: 2,
        step_type: 'decision',
        timestamp: new Date(Date.now() - 20000).toISOString(),
        duration_ms: 510,
        confidence_score: 0.42,
        reasoning_summary: 'Context Firewall Interception: Detected numerical conflict (Source A $14.2M vs Source B $18.5M). Enforcing verified internal spec.',
        status: 'completed',
        input_data: { conflict_type: 'Numerical', sourceA: '$14.2M', sourceB: '$18.5M' },
        output_data: { resolution: 'Accepted Source A ($14.2M), Rejected unverified Source B.' }
      },
      {
        step_id: 'step-3',
        step_number: 3,
        step_type: 'llm_call',
        timestamp: new Date().toISOString(),
        duration_ms: 1420,
        confidence_score: 0.96,
        reasoning_summary: 'Generating sanitized financial analysis response with provenance tracking.',
        status: 'completed',
        input_data: { prompt: taskPrompt },
        output_data: { response: 'Acme Corp Q3 verified revenue was $14.2M as confirmed by spec records.' }
      }
    ];
  }

  if (scenarioId === 'api_failure_recovery' || injectChaos) {
    return [
      {
        step_id: 'step-1',
        step_number: 1,
        step_type: 'tool_call',
        timestamp: new Date(Date.now() - 45000).toISOString(),
        duration_ms: 410,
        tool_name: 'inspect_pool_settings',
        confidence_score: 0.95,
        reasoning_summary: 'Inspecting current connection pool parameters in backend module.',
        status: 'completed',
        input_data: { path: 'src/db/connection.py' },
        output_data: { current_max_connections: 5 }
      },
      {
        step_id: 'step-2',
        step_number: 2,
        step_type: 'llm_call',
        timestamp: new Date(Date.now() - 30000).toISOString(),
        duration_ms: 1250,
        confidence_score: 0.89,
        reasoning_summary: 'Generating optimized async pool config with explicit overflow parameters.',
        status: 'completed',
        input_data: { target_pool_size: 20 },
        output_data: { proposed_config: 'create_async_engine(DATABASE_URL, pool_size=20)' }
      },
      {
        step_id: 'step-3',
        step_number: 3,
        step_type: 'tool_call',
        timestamp: new Date(Date.now() - 15000).toISOString(),
        duration_ms: 890,
        tool_name: 'execute_sql_migration',
        confidence_score: 0.32,
        reasoning_summary: 'Executing schema migration. Encountered invalid max_overflow parameter error.',
        status: 'failed',
        error: 'DatabaseError: Connection refused (invalid pool parameter max_overflow=NaN)',
        input_data: { sql: 'ALTER SYSTEM SET max_overflow = NaN;' },
        output_data: { error: 'Syntax error' }
      },
      {
        step_id: 'step-4',
        step_number: 4,
        step_type: 'decision',
        timestamp: new Date(Date.now() - 5000).toISOString(),
        duration_ms: 620,
        confidence_score: 0.78,
        reasoning_summary: 'Recovery Engine intervention: Rolling back to safe Checkpoint #2 and applying verified patch.',
        status: 'completed',
        was_recovered: true,
        input_data: { action: 'rollback', target_step: 2 },
        output_data: { state_restored: true }
      },
      {
        step_id: 'step-5',
        step_number: 5,
        step_type: 'tool_call',
        timestamp: new Date().toISOString(),
        duration_ms: 740,
        tool_name: 'apply_safe_patch',
        confidence_score: 0.98,
        reasoning_summary: 'Applying safe connection pool patch (max_overflow=10). All tests passing.',
        status: 'completed',
        was_recovered: true,
        input_data: { max_overflow: 10 },
        output_data: { status: 'SUCCESS', tests_passed: 14 }
      }
    ];
  }

  // Default "Research a company" / "Analyze a document"
  return [
    {
      step_id: 'step-1',
      step_number: 1,
      step_type: 'tool_call',
      timestamp: new Date(Date.now() - 35000).toISOString(),
      duration_ms: 450,
      tool_name: 'web_search_overview',
      confidence_score: 0.96,
      reasoning_summary: 'Searching overview and core AI foundation model milestones.',
      status: 'completed',
      input_data: { query: 'Anthropic overview Claude models 2026' },
      output_data: { matches: ['Claude Sonnet 4.6', 'Claude Opus 4'] }
    },
    {
      step_id: 'step-2',
      step_number: 2,
      step_type: 'tool_call',
      timestamp: new Date(Date.now() - 25000).toISOString(),
      duration_ms: 620,
      tool_name: 'fetch_funding_data',
      confidence_score: 0.92,
      reasoning_summary: 'Fetching funding round investments & corporate partnership metrics.',
      status: 'completed',
      input_data: { query: 'Anthropic funding round valuation' },
      output_data: { funding_total: '$7.3B+', primary_investors: ['Amazon', 'Google'] }
    },
    {
      step_id: 'step-3',
      step_number: 3,
      step_type: 'llm_call',
      timestamp: new Date(Date.now() - 12000).toISOString(),
      duration_ms: 1850,
      confidence_score: 0.95,
      reasoning_summary: 'Synthesizing competitive advantage analysis and enterprise market brief.',
      status: 'completed',
      input_data: { prompt: 'Compile investment brief for Anthropic' },
      output_data: { investment_brief_ready: true }
    },
    {
      step_id: 'step-4',
      step_number: 4,
      step_type: 'tool_call',
      timestamp: new Date().toISOString(),
      duration_ms: 540,
      tool_name: 'save_brief_artifact',
      confidence_score: 0.99,
      reasoning_summary: 'Persisting final enterprise brief artifact and attaching provenance tags.',
      status: 'completed',
      input_data: { artifact_name: 'anthropic_investment_brief.md' },
      output_data: { status: 'SAVED', bytes: 4820 }
    }
  ];
}
