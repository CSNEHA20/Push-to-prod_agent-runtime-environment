import React from 'react';
import { FileText, Database, User } from 'lucide-react';

/**
 * ProvenanceTag component
 * Displays inline source metadata: source name + confidence score percentage badge
 */
export default function ProvenanceTag({ sourceName, confidence, type = 'document', className = '' }) {
  const numConfidence = typeof confidence === 'number' 
    ? (confidence > 1 ? confidence / 100 : confidence)
    : parseFloat(confidence) || 0;

  const formattedPercent = `${Math.round(numConfidence * 100)}%`;

  const getConfidenceBadgeColor = (val) => {
    if (val >= 0.8) return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
    if (val >= 0.5) return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
    return 'bg-red-500/15 text-red-400 border-red-500/30';
  };

  const getTypeIcon = () => {
    switch (type?.toLowerCase()) {
      case 'api':
        return <Database className="w-3 h-3 text-arc-secondary" />;
      case 'user':
        return <User className="w-3 h-3 text-arc-tertiary" />;
      case 'document':
      default:
        return <FileText className="w-3 h-3 text-arc-primary" />;
    }
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono border bg-arc-bg/90 border-arc-outline text-arc-textPrimary shadow-sm hover:border-arc-primary/50 transition-colors select-none ${className}`}
      title={`Source: ${sourceName} (${formattedPercent} confidence)`}
    >
      {getTypeIcon()}
      <span className="font-medium text-arc-textPrimary truncate max-w-[150px]">
        {sourceName}
      </span>
      <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold border ${getConfidenceBadgeColor(numConfidence)}`}>
        {formattedPercent}
      </span>
    </span>
  );
}
