import React from 'react';
import { 
  FileText, 
  Database, 
  User, 
  CheckCircle2, 
  XCircle, 
  ShieldAlert, 
  ArrowRight, 
  Filter,
  Check,
  Zap
} from 'lucide-react';

/**
 * ContextGraph component
 * Displays a 3-column visual diagram showing context flow:
 * Left: Raw Sources (with relevance scores)
 * Middle: Firewall (filter statistics)
 * Right: To Claude (passed sources only)
 */
export default function ContextGraph({ sources = [] }) {
  // Default mock sources if none provided
  const defaultSources = [
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
  ];

  const sourceList = sources && sources.length > 0 ? sources : defaultSources;

  const passedSources = sourceList.filter(s => s.status === 'PASSED' || s.status === 'passed');
  const rejectedSources = sourceList.filter(s => s.status === 'REJECTED' || s.status === 'rejected');
  const totalCount = sourceList.length;
  const passedCount = passedSources.length;
  const rejectedCount = rejectedSources.length;
  const passRate = totalCount > 0 ? Math.round((passedCount / totalCount) * 100) : 0;

  const getTypeIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'api':
        return <Database className="w-4 h-4 text-arc-secondary" />;
      case 'user':
        return <User className="w-4 h-4 text-arc-tertiary" />;
      case 'document':
      default:
        return <FileText className="w-4 h-4 text-arc-primary" />;
    }
  };

  const renderSourceCard = (src, showDetails = true) => {
    const scoreVal = typeof src.score === 'number' 
      ? (src.score > 1 ? src.score / 100 : src.score) 
      : parseFloat(src.score) || 0;
    const percentScore = Math.round(scoreVal * 100);
    const isPassed = src.status === 'PASSED' || src.status === 'passed';

    return (
      <div 
        key={src.id || src.name}
        className={`p-3.5 rounded-lg border transition-all font-mono text-xs ${
          isPassed 
            ? 'bg-arc-surface/80 border-arc-outline hover:border-emerald-500/40 shadow-sm' 
            : 'bg-red-500/5 border-red-500/30 hover:border-red-500/50'
        }`}
      >
        {/* Header row */}
        <div className="flex items-center justify-between gap-2 mb-2">
          <div className="flex items-center gap-2 min-w-0">
            <div className="p-1 rounded bg-arc-bg border border-arc-outline shrink-0">
              {getTypeIcon(src.type)}
            </div>
            <span className="font-semibold text-arc-textPrimary truncate" title={src.name}>
              {src.name}
            </span>
          </div>

          {/* Status Badge */}
          {isPassed ? (
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 shrink-0">
              <CheckCircle2 className="w-3 h-3" />
              PASSED
            </span>
          ) : (
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/15 text-red-400 border border-red-500/30 flex items-center gap-1 shrink-0">
              <XCircle className="w-3 h-3" />
              REJECTED
            </span>
          )}
        </div>

        {/* Relevance Score Bar */}
        <div className="space-y-1 mb-2">
          <div className="flex justify-between text-[11px] text-arc-textSecondary">
            <span>Relevance Score</span>
            <span className={`font-bold ${isPassed ? 'text-emerald-400' : 'text-red-400'}`}>
              {percentScore}%
            </span>
          </div>
          <div className="w-full h-1.5 bg-arc-bg rounded-full overflow-hidden border border-arc-outline/50">
            <div 
              className={`h-full rounded-full transition-all duration-500 ${
                isPassed ? 'bg-gradient-to-r from-emerald-500 to-teal-400' : 'bg-gradient-to-r from-red-500 to-amber-500'
              }`}
              style={{ width: `${percentScore}%` }}
            />
          </div>
        </div>

        {/* Rejection reason if rejected */}
        {!isPassed && src.reason && (
          <div className="mt-2 text-[10px] p-2 rounded bg-red-500/10 border border-red-500/20 text-red-300 flex items-start gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-red-400 shrink-0 mt-0.5" />
            <span><strong>Reason:</strong> {src.reason}</span>
          </div>
        )}

        {/* Snippet preview */}
        {showDetails && src.snippet && (
          <p className="mt-2 text-[11px] text-arc-textSecondary line-clamp-2 italic bg-arc-bg/50 p-1.5 rounded border border-arc-outline/30">
            "{src.snippet}"
          </p>
        )}
      </div>
    );
  };

  return (
    <div className="bg-arc-surface border border-arc-outline rounded-xl p-5 font-mono space-y-4">
      <div className="flex items-center justify-between border-b border-arc-outline pb-3">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-arc-secondary" />
          <h3 className="text-sm font-bold text-arc-textPrimary uppercase tracking-wider">
            Context Filtering Pipeline Flow
          </h3>
        </div>
        <span className="text-xs text-arc-textSecondary">
          Total Context Chunks: <strong className="text-arc-textPrimary">{totalCount}</strong>
        </span>
      </div>

      {/* 3-Column Diagram Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-stretch">
        {/* Left Column: Raw Sources (5 cols) */}
        <div className="lg:col-span-5 flex flex-col space-y-3 bg-arc-bg/60 border border-arc-outline rounded-xl p-4">
          <div className="flex items-center justify-between border-b border-arc-outline/60 pb-2">
            <h4 className="text-xs font-bold text-arc-textPrimary uppercase tracking-wider flex items-center gap-1.5">
              <Database className="w-4 h-4 text-arc-primary" />
              Raw Sources ({totalCount})
            </h4>
            <span className="text-[10px] text-arc-textSecondary">Unfiltered Context</span>
          </div>

          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
            {sourceList.map(src => renderSourceCard(src, true))}
          </div>
        </div>

        {/* Middle Column: Firewall Engine Stats (2 cols) */}
        <div className="lg:col-span-2 flex flex-col justify-center items-center py-4 px-2 bg-arc-bg/80 border border-arc-secondary/30 rounded-xl relative overflow-hidden space-y-4 shadow-inner">
          <div className="absolute inset-0 bg-arc-secondary/5 pointer-events-none" />

          {/* Firewall Badge */}
          <div className="p-3 bg-arc-secondary/15 rounded-full border border-arc-secondary/40 text-arc-secondary animate-pulse shadow-lg">
            <ShieldAlert className="w-7 h-7" />
          </div>

          <div className="text-center space-y-1 z-10">
            <span className="text-xs font-bold uppercase tracking-wider text-arc-textPrimary block">
              Firewall
            </span>
            <span className="text-[10px] text-arc-textSecondary block">
              Semantic Filter Engine
            </span>
          </div>

          {/* Filter Stats */}
          <div className="w-full space-y-2 text-xs z-10 font-mono">
            <div className="bg-arc-surface border border-emerald-500/30 p-2 rounded-lg text-center">
              <span className="text-[10px] text-arc-textSecondary block">PASSED</span>
              <span className="text-lg font-extrabold text-emerald-400">{passedCount}</span>
            </div>

            <div className="bg-arc-surface border border-red-500/30 p-2 rounded-lg text-center">
              <span className="text-[10px] text-arc-textSecondary block">REJECTED</span>
              <span className="text-lg font-extrabold text-red-400">{rejectedCount}</span>
            </div>

            <div className="bg-arc-surface border border-arc-outline p-2 rounded-lg text-center">
              <span className="text-[10px] text-arc-textSecondary block">PASS RATE</span>
              <span className="text-sm font-bold text-arc-primary">{passRate}%</span>
            </div>
          </div>

          <div className="hidden lg:flex items-center justify-between w-full text-arc-secondary px-2 pt-2">
            <ArrowRight className="w-4 h-4 mx-auto animate-bounce" />
          </div>
        </div>

        {/* Right Column: To Claude (5 cols) */}
        <div className="lg:col-span-5 flex flex-col space-y-3 bg-arc-bg/60 border border-emerald-500/20 rounded-xl p-4">
          <div className="flex items-center justify-between border-b border-arc-outline/60 pb-2">
            <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
              <Zap className="w-4 h-4 text-emerald-400" />
              To Claude ({passedCount})
            </h4>
            <span className="text-[10px] text-emerald-400/80 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              Sanitized Prompt Context
            </span>
          </div>

          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
            {passedSources.length > 0 ? (
              passedSources.map(src => renderSourceCard(src, true))
            ) : (
              <div className="p-8 text-center text-arc-textSecondary text-xs">
                No sources passed the firewall filter.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
