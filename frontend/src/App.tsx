import React, { useEffect, useRef, useState } from 'react';
import { Header } from './components/layout/Header';
import { TickerBar } from './components/market/TickerBar';
import { Watchlist } from './components/market/Watchlist';
import { TradingViewChart } from './components/chart/TradingViewChart';
import { SignalPanelShell } from './components/intelligence/SignalPanelShell';
import { BottomMetricsShell } from './components/layout/BottomMetricsShell';
import { TradeDecisionHero } from './components/trade-decision/TradeDecisionHero';
import { ProfileContextBar } from './components/profiles/ProfileContextBar';
import { ScalpHero } from './components/scalp/ScalpHero';
import { useMarketStore } from './stores/marketStore';
import { MarketWebSocketClient } from './services/websocketService';
import { PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen, Maximize2, Minimize2 } from 'lucide-react';

export const App: React.FC = () => {
  const {
    symbol,
    timeframe,
    selectedProfileId,
    loadHistoricalData,
    handleWebSocketMessage,
    setConnectionState,
  } = useMarketStore();

  const isScalpMode = selectedProfileId === 'SCALP_1M_V1';

  const [showWatchlist, setShowWatchlist] = useState<boolean>(() => typeof window !== 'undefined' ? window.innerWidth >= 1024 : true);
  const [showIntelligence, setShowIntelligence] = useState<boolean>(() => typeof window !== 'undefined' ? window.innerWidth >= 1280 : true);

  const wsClientRef = useRef<MarketWebSocketClient | null>(null);

  // Initial historical data load
  useEffect(() => {
    loadHistoricalData();
  }, [symbol, timeframe]);

  // Real-time WebSocket connection lifecycle
  useEffect(() => {
    const client = new MarketWebSocketClient(
      symbol,
      timeframe,
      (msg) => handleWebSocketMessage(msg),
      (status, message) => setConnectionState(status, message)
    );

    wsClientRef.current = client;
    client.connect();

    return () => {
      client.disconnect();
      wsClientRef.current = null;
    };
  }, [symbol, timeframe]);

  const isFullWidthChart = !showWatchlist && !showIntelligence;

  const toggleFullWidth = () => {
    if (isFullWidthChart) {
      setShowWatchlist(true);
      setShowIntelligence(true);
    } else {
      setShowWatchlist(false);
      setShowIntelligence(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background text-text-primary overflow-x-hidden">
      {/* Header */}
      <Header />

      {/* 24h Ticker & Symbol Metrics Bar */}
      <TickerBar />

      {/* Main Terminal Grid Layout */}
      <main className="flex-1 p-2 sm:p-3 flex flex-col gap-2.5 sm:gap-3 max-w-[1920px] mx-auto w-full overflow-x-hidden">
        {/* Phase 12: Multi-Timeframe Profile Context Synchronizer Bar */}
        <ProfileContextBar />

        {/* Hero Decision Panel — ScalpHero when SCALP profile, TradeDecisionHero otherwise */}
        {isScalpMode ? <ScalpHero /> : <TradeDecisionHero />}

        {/* Chart Viewport Controls & Layout Actions */}
        <div className="flex flex-wrap items-center justify-between px-1 text-xs font-mono text-slate-400 gap-2">
          <div className="flex items-center gap-1.5 sm:gap-2">
            <button
              onClick={() => setShowWatchlist(!showWatchlist)}
              className={`px-2.5 sm:px-3 py-1.5 rounded-lg border flex items-center gap-1.5 transition text-[11px] sm:text-xs min-h-[36px] ${
                showWatchlist
                  ? 'bg-slate-900 border-slate-700 text-slate-200 shadow-md'
                  : 'bg-slate-950/60 border-slate-800 text-slate-500 hover:text-slate-300'
              }`}
              title={showWatchlist ? 'Hide Watchlist' : 'Show Watchlist'}
            >
              {showWatchlist ? <PanelLeftClose className="w-4 h-4 text-indigo-400" /> : <PanelLeftOpen className="w-4 h-4" />}
              <span>Watchlist</span>
            </button>

            <button
              onClick={() => setShowIntelligence(!showIntelligence)}
              className={`px-2.5 sm:px-3 py-1.5 rounded-lg border flex items-center gap-1.5 transition text-[11px] sm:text-xs min-h-[36px] ${
                showIntelligence
                  ? 'bg-slate-900 border-slate-700 text-slate-200 shadow-md'
                  : 'bg-slate-950/60 border-slate-800 text-slate-500 hover:text-slate-300'
              }`}
              title={showIntelligence ? 'Hide Signal Panel' : 'Show Signal Panel'}
            >
              {showIntelligence ? <PanelRightClose className="w-4 h-4 text-indigo-400" /> : <PanelRightOpen className="w-4 h-4" />}
              <span>Signal Panel</span>
            </button>
          </div>

          <button
            onClick={toggleFullWidth}
            className={`px-2.5 sm:px-3 py-1.5 rounded-lg border flex items-center gap-1.5 transition text-[11px] sm:text-xs min-h-[36px] ${
              isFullWidthChart
                ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-600/30'
                : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            {isFullWidthChart ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            <span className="hidden xs:inline">{isFullWidthChart ? 'Restore Panels' : 'Full Chart Mode'}</span>
            <span className="xs:hidden">{isFullWidthChart ? 'Restore' : 'Full'}</span>
          </button>
        </div>

        {/* Top Split: Watchlist + Main Chart + Signal Panel (Stacked on mobile, side-by-side on desktop lg+) */}
        <div className="flex-1 flex flex-col lg:flex-row gap-2.5 sm:gap-3 w-full max-w-full">
          {/* Left Watchlist (Horizontal strip on mobile/tablet, vertical sidebar on desktop) */}
          {showWatchlist && (
            <div className="w-full lg:w-auto transition-all shrink-0">
              <Watchlist />
            </div>
          )}

          {/* Center Realtime Candlestick Chart */}
          <div className="flex-1 min-w-0 w-full">
            <TradingViewChart />
          </div>

          {/* Right AI Signal Panel Shell */}
          {showIntelligence && (
            <div className="w-full lg:w-auto transition-all shrink-0">
              <SignalPanelShell />
            </div>
          )}
        </div>

        {/* Bottom Tabbed Metrics Shell */}
        <BottomMetricsShell />

        {/* Institutional Safety Disclaimer Footer */}
        <footer className="mt-2 py-2 px-3 bg-slate-950 border border-slate-800/80 rounded-lg text-center text-[10px] font-mono text-slate-500 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 text-slate-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            <span>SHADOW / ANALYSIS ONLY</span>
          </div>
          <div>
            ANALYTICAL TRADE PLAN — NOT A GUARANTEED PREDICTION — ZERO AUTOMATED EXECUTION
          </div>
          <div className="text-slate-600">
            Crypto AI Trading Intelligence Platform v1.0.0
          </div>
        </footer>
      </main>
    </div>
  );
};

export default App;
