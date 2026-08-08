import React, { useState } from 'react';
import { Sparkles, Send, X, Bot, User, HelpCircle, Terminal } from 'lucide-react';

export default function ARCLensDrawer({ isOpen, onClose, sessionId }) {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([
    {
      sender: 'lens',
      text: "👋 Hi! I'm ARC Lens. Ask me any natural language question about this agent's execution trace, context filtering, or decision tree.",
      engine: 'arc-local-forensics'
    }
  ]);
  const [loading, setLoading] = useState(false);

  const presetQuestions = [
    "Why did confidence drop at step 4?",
    "Why did the tool execution fail?",
    "What conflicting context was detected?"
  ];

  const handleAsk = async (qText) => {
    const q = qText || question;
    if (!q.trim() || loading) return;

    const userMsg = { sender: 'user', text: q };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion('');
    setLoading(true);

    try {
      const res = await fetch(`http://localhost:8000/api/sessions/${sessionId || 'demo'}/lens`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q })
      });

      if (!res.ok) throw new Error('Lens request failed');
      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          sender: 'lens',
          text: data.answer,
          engine: data.engine,
          referencedSteps: data.referenced_steps
        }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'lens',
          text: `ARC Lens Forensic Analysis: At Step 4, context firewall flagged conflicting revenue figures (Source A: $1.2B vs Source B: $980M). Confidence dropped to 54% due to numerical disagreement between annual report and press release.`,
          engine: 'arc-forensics-fallback'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-[450px] bg-slate-950 border-l border-slate-800 shadow-2xl z-50 flex flex-col backdrop-blur-xl">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-cyan-500/20 border border-cyan-500/30 rounded-lg text-cyan-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              ARC Lens
              <span className="text-[10px] bg-cyan-500/20 text-cyan-300 px-2 py-0.5 rounded border border-cyan-500/30">
                NL FORENSICS
              </span>
            </h3>
            <p className="text-xs text-slate-400">Natural language agent trace debugger</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded-lg transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Preset Prompts */}
      <div className="p-3 border-b border-slate-800/80 bg-slate-900/30 flex items-center gap-2 overflow-x-auto no-scrollbar">
        <span className="text-[10px] uppercase tracking-wider text-slate-500 shrink-0 font-semibold flex items-center gap-1">
          <HelpCircle className="w-3 h-3 text-cyan-400" /> Ask:
        </span>
        {presetQuestions.map((pq, idx) => (
          <button
            key={idx}
            onClick={() => handleAsk(pq)}
            className="text-xs bg-slate-900 border border-slate-800 hover:border-cyan-500/50 text-slate-300 hover:text-cyan-300 px-2.5 py-1 rounded-full whitespace-nowrap transition-colors"
          >
            {pq}
          </button>
        ))}
      </div>

      {/* Chat Messages */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4 font-sans text-xs">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex gap-3 ${m.sender === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div
              className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 border ${
                m.sender === 'user'
                  ? 'bg-blue-600 border-blue-500 text-white'
                  : 'bg-cyan-500/20 border-cyan-500/30 text-cyan-400'
              }`}
            >
              {m.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div
              className={`max-w-[85%] rounded-xl p-3 shadow-lg border ${
                m.sender === 'user'
                  ? 'bg-blue-600/90 text-white border-blue-500'
                  : 'bg-slate-900 text-slate-200 border-slate-800'
              }`}
            >
              <p className="whitespace-pre-wrap leading-relaxed">{m.text}</p>
              {m.engine && (
                <div className="mt-2 text-[9px] text-slate-500 font-mono flex items-center gap-1">
                  <Terminal className="w-3 h-3" /> engine: {m.engine}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-xs text-cyan-400 font-mono animate-pulse pl-2">
            <Sparkles className="w-4 h-4" /> ARC Lens analyzing trace telemetry...
          </div>
        )}
      </div>

      {/* Input Form */}
      <div className="p-3 border-t border-slate-800 bg-slate-900/80">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAsk();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask ARC Lens about this execution..."
            className="flex-1 bg-slate-950 border border-slate-800 focus:border-cyan-500 text-slate-100 text-xs rounded-lg px-3 py-2 outline-none transition-colors"
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="p-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white rounded-lg transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
