import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Layers, Terminal, Activity, Shield, RefreshCw, Cpu, CheckCircle2, AlertTriangle } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Sessions from './pages/Sessions';
import Playground from './pages/Playground';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connected');

  useEffect(() => {
    // Check backend health
    const checkBackend = async () => {
      try {
        const res = await fetch('http://localhost:8000/health');
        if (res.ok) {
          setConnectionStatus('connected');
        } else {
          setConnectionStatus('degraded');
        }
      } catch (err) {
        setConnectionStatus('disconnected');
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectSession = (sessionId) => {
    setSelectedSessionId(sessionId);
    setActiveTab('sessions');
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard onSelectSession={handleSelectSession} />;
      case 'sessions':
        return <Sessions onSelectSession={handleSelectSession} />;
      case 'playground':
        return <Playground />;
      default:
        return <Dashboard onSelectSession={handleSelectSession} />;
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-[#F1F5F9] flex flex-col font-sans antialiased">
      {/* Top Header */}
      <header className="h-16 border-b border-[#1E1E2E] bg-[#12121A]/90 backdrop-blur sticky top-0 z-50 px-6 flex items-center justify-between">
        {/* Monospace Logo */}
        <div className="flex items-center space-x-3">
          <div className="h-9 px-3 rounded-lg bg-[#6366F1] flex items-center justify-center font-mono font-bold text-white text-base shadow-lg shadow-[#6366F1]/20 tracking-wider">
            ARC
          </div>
          <div>
            <h1 className="font-mono font-bold text-sm text-[#F1F5F9] leading-none tracking-wide">
              AGENT RUNTIME CORE
            </h1>
            <p className="text-[11px] text-[#94A3B8] font-mono mt-0.5">
              Reliability & Traceability Layer for Claude AI Agents
            </p>
          </div>
        </div>

        {/* Connection Status Indicator */}
        <div className="flex items-center space-x-4 font-mono text-xs">
          <div className="flex items-center space-x-2 bg-[#0A0A0F] border border-[#1E1E2E] px-3 py-1.5 rounded-full">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                connectionStatus === 'connected'
                  ? 'bg-[#10B981] animate-pulse'
                  : connectionStatus === 'degraded'
                  ? 'bg-[#F59E0B]'
                  : 'bg-[#EF4444]'
              }`}
            ></span>
            <span className="text-[#94A3B8] capitalize">
              System: <strong className="text-[#F1F5F9]">{connectionStatus}</strong>
            </span>
          </div>
        </div>
      </header>

      {/* Main Layout: Sidebar (240px) + Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar Navigation (240px wide) */}
        <aside className="w-[240px] bg-[#12121A] border-r border-[#1E1E2E] p-4 flex flex-col justify-between shrink-0 font-mono text-xs">
          <div className="space-y-6">
            <div className="space-y-1">
              <span className="px-3 text-[10px] text-[#94A3B8] uppercase tracking-wider font-semibold">
                Navigation
              </span>

              <button
                onClick={() => setActiveTab('dashboard')}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors font-medium ${
                  activeTab === 'dashboard'
                    ? 'bg-[#6366F1]/10 text-[#6366F1] border border-[#6366F1]/20 font-semibold'
                    : 'text-[#94A3B8] hover:text-[#F1F5F9] hover:bg-[#1E1E2E]/50'
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                <span>Dashboard</span>
              </button>

              <button
                onClick={() => setActiveTab('sessions')}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors font-medium ${
                  activeTab === 'sessions'
                    ? 'bg-[#6366F1]/10 text-[#6366F1] border border-[#6366F1]/20 font-semibold'
                    : 'text-[#94A3B8] hover:text-[#F1F5F9] hover:bg-[#1E1E2E]/50'
                }`}
              >
                <Layers className="w-4 h-4" />
                <span>Sessions</span>
              </button>

              <button
                onClick={() => setActiveTab('playground')}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors font-medium ${
                  activeTab === 'playground'
                    ? 'bg-[#6366F1]/10 text-[#6366F1] border border-[#6366F1]/20 font-semibold'
                    : 'text-[#94A3B8] hover:text-[#F1F5F9] hover:bg-[#1E1E2E]/50'
                }`}
              >
                <Terminal className="w-4 h-4" />
                <span>Playground</span>
              </button>
            </div>

            {/* Engine Overview Widget in Sidebar */}
            <div className="space-y-2 pt-4 border-t border-[#1E1E2E]">
              <span className="px-3 text-[10px] text-[#94A3B8] uppercase tracking-wider font-semibold">
                Engines
              </span>
              <div className="space-y-1.5 px-3">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="flex items-center gap-1.5 text-slate-300">
                    <Activity className="w-3 h-3 text-[#6366F1]" />
                    Flight Recorder
                  </span>
                  <span className="text-[#10B981]">Active</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="flex items-center gap-1.5 text-slate-300">
                    <Shield className="w-3 h-3 text-[#F59E0B]" />
                    Context Firewall
                  </span>
                  <span className="text-[#10B981]">Active</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="flex items-center gap-1.5 text-slate-300">
                    <RefreshCw className="w-3 h-3 text-[#10B981]" />
                    Recovery Engine
                  </span>
                  <span className="text-[#10B981]">Active</span>
                </div>
              </div>
            </div>
          </div>

          <div className="p-3 bg-[#0A0A0F] border border-[#1E1E2E] rounded-lg text-[11px] text-[#94A3B8]">
            <div>ARC Version: <strong className="text-[#F1F5F9]">v1.0.0</strong></div>
            <div>Model: <strong className="text-[#6366F1]">claude-sonnet-4-6</strong></div>
          </div>
        </aside>

        {/* Main Content Area (Right side) */}
        <main className="flex-1 overflow-y-auto p-6 bg-[#0A0A0F]">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}
