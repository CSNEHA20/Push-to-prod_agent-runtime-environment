import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Layers, Terminal, Activity, Shield, RefreshCw } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Sessions from './pages/Sessions';
import Playground from './pages/Playground';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connected');

  useEffect(() => {
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
        return <Playground onSelectSession={handleSelectSession} />;
      default:
        return <Dashboard onSelectSession={handleSelectSession} />;
    }
  };

  return (
    <div className="min-h-screen bg-arc-bg text-arc-textPrimary flex flex-col font-sans antialiased">
      {/* Top Header (64px) */}
      <header className="h-16 border-b border-arc-outline bg-arc-surface/90 backdrop-blur sticky top-0 z-50 px-6 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-9 px-3 rounded-lg bg-arc-primary flex items-center justify-center font-mono font-bold text-[#131316] text-base shadow-lg shadow-arc-primary/20 tracking-wider">
            ARC
          </div>
          <div>
            <h1 className="font-mono font-bold text-sm text-arc-textPrimary leading-none tracking-wide">
              AGENT RUNTIME CORE
            </h1>
            <p className="text-[11px] text-arc-textSecondary font-mono mt-0.5">
              Reliability & Traceability Layer for Claude AI Agents
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-4 font-mono text-xs">
          <div className="flex items-center space-x-2 bg-arc-bg border border-arc-outline px-3 py-1.5 rounded-full">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                connectionStatus === 'connected'
                  ? 'bg-arc-tertiary animate-pulse'
                  : connectionStatus === 'degraded'
                  ? 'bg-arc-secondary'
                  : 'bg-arc-error'
              }`}
            ></span>
            <span className="text-arc-textSecondary capitalize">
              System: <strong className="text-arc-textPrimary">{connectionStatus}</strong>
            </span>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar Navigation (240px) */}
        <aside className="w-[240px] bg-arc-surface border-r border-arc-outline p-4 flex flex-col justify-between shrink-0 font-mono text-xs">
          <div className="space-y-6">
            <div className="space-y-1">
              <span className="px-3 text-[10px] text-arc-textSecondary uppercase tracking-wider font-semibold">
                Navigation
              </span>

              <button
                onClick={() => setActiveTab('dashboard')}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors font-medium ${
                  activeTab === 'dashboard'
                    ? 'bg-arc-primary/10 text-arc-primary border border-arc-primary/20 font-semibold'
                    : 'text-arc-textSecondary hover:text-arc-textPrimary hover:bg-arc-outline/50'
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                <span>Dashboard</span>
              </button>

              <button
                onClick={() => setActiveTab('sessions')}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors font-medium ${
                  activeTab === 'sessions'
                    ? 'bg-arc-primary/10 text-arc-primary border border-arc-primary/20 font-semibold'
                    : 'text-arc-textSecondary hover:text-arc-textPrimary hover:bg-arc-outline/50'
                }`}
              >
                <Layers className="w-4 h-4" />
                <span>Sessions</span>
              </button>

              <button
                onClick={() => setActiveTab('playground')}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors font-medium ${
                  activeTab === 'playground'
                    ? 'bg-arc-primary/10 text-arc-primary border border-arc-primary/20 font-semibold'
                    : 'text-arc-textSecondary hover:text-arc-textPrimary hover:bg-arc-outline/50'
                }`}
              >
                <Terminal className="w-4 h-4" />
                <span>Playground</span>
              </button>
            </div>

            <div className="space-y-2 pt-4 border-t border-arc-outline">
              <span className="px-3 text-[10px] text-arc-textSecondary uppercase tracking-wider font-semibold">
                Engines
              </span>
              <div className="space-y-1.5 px-3">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="flex items-center gap-1.5 text-arc-textPrimary">
                    <Activity className="w-3 h-3 text-arc-primary" />
                    Flight Recorder
                  </span>
                  <span className="text-arc-tertiary">Active</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="flex items-center gap-1.5 text-arc-textPrimary">
                    <Shield className="w-3 h-3 text-arc-secondary" />
                    Context Firewall
                  </span>
                  <span className="text-arc-tertiary">Active</span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="flex items-center gap-1.5 text-arc-textPrimary">
                    <RefreshCw className="w-3 h-3 text-arc-tertiary" />
                    Recovery Engine
                  </span>
                  <span className="text-arc-tertiary">Active</span>
                </div>
              </div>
            </div>
          </div>

          <div className="p-3 bg-arc-bg border border-arc-outline rounded-lg text-[11px] text-arc-textSecondary">
            <div>ARC Version: <strong className="text-arc-textPrimary">v1.0.0</strong></div>
            <div>Model: <strong className="text-arc-primary">claude-sonnet-4-6</strong></div>
          </div>
        </aside>

        <main className="flex-1 overflow-y-auto p-6 bg-arc-bg">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}
