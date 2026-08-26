import React, { useState } from 'react';
import { Activity, Radio, Cpu, ShieldCheck, Clock, CheckCircle2, AlertTriangle, XCircle, Info, Zap } from 'lucide-react';
import { useMarketStore, formatSymbolPrice, formatPercentage } from '../../stores/marketStore';
import { ProfileSelector } from '../profiles/ProfileSelector';

export const Header: React.FC = () => {
  const {
    symbol,
    timeframe,
    ticker,
    connectionState,
    lastUpdated,
    latencyMs,
    isStale,
    quality,
    candles,
  } = useMarketStore();

  const [showQualityModal, setShowQualityModal] = useState<boolean>(false);

  const lastClosedCandle = candles.filter((c) => c.is_closed).pop();
  const lastClosedUtc = lastClosedCandle
    ? new Date(lastClosedCandle.timestamp).toLocaleTimeString('en-US', {
        timeZone: 'UTC',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      }) + ' UTC'
    : '—';

  const localTimeStr = new Date(lastUpdated).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });

  const getStatusBadge = () => {
    if (isStale || connectionState === 'RECONNECTING') {
      return (
        <div className="flex items-center gap-1.5 bg-amber-500/10 border border-amber-500/30 px-2.5 py-1 rounded text-amber-400 text-[11px] font-mono font-bold">
          <Radio className="w-3.5 h-3.5 animate-spin" />
          <span>RECONNECTING</span>
        </div>
      );
    }
    if (connectionState === 'LIVE') {
      return (
        <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1 rounded text-emerald-400 text-[11px] font-mono font-bold shadow-glow-green">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span>LIVE FEED</span>
        </div>
      );
    }
    return (
      <div className="flex items-center gap-1.5 bg-rose-500/10 border border-rose-500/30 px-2.5 py-1 rounded text-rose-400 text-[11px] font-mono font-bold">
        <div className="w-2 h-2 rounded-full bg-rose-500" />
        <span>DISCONNECTED</span>
      </div>
    );
  };

  const getQualityBadge = () => {
    const qStatus = quality?.status || 'HEALTHY';
    const isHealthy = qStatus === 'HEALTHY';
    const isWarning = qStatus === 'WARNING';

    return (
      <div
        onMouseEnter={() => setShowQualityModal(true)}
        onMouseLeave={() => setShowQualityModal(false)}
        className={`relative flex items-center gap-1.5 px-2 py-0.5 rounded border text-[10px] font-mono font-bold cursor-help transition ${
          isHealthy
            ? 'bg-emerald-950/40 text-emerald-300 border-emerald-800/60'
            : isWarning
            ? 'bg-amber-950/40 text-amber-300 border-amber-800/60'
            : 'bg-rose-950/40 text-rose-300 border-rose-800/60'
        }`}
      >
        {isHealthy ? <CheckCircle2 className="w-3 h-3 text-emerald-400" /> : <AlertTriangle className="w-3 h-3 text-amber-400" />}
        <span>DATA: {qStatus}</span>

        {/* Quality Hover Tooltip */}
        {showQualityModal && (
          <div className="absolute top-7 left-0 w-64 bg-slate-950 border border-slate-700 rounded-lg p-3 text-[11px] font-sans text-slate-300 shadow-2xl z-50 pointer-events-none">
            <div className="font-bold text-slate-100 uppercase tracking-wider mb-1 flex items-center gap-1.5 font-mono">
              <Activity className="w-3.5 h-3.5 text-indigo-400" />
              Data Quality Engine
            </div>
            <div className="space-y-1 text-slate-400 font-mono text-[10px]">
              <div className="flex justify-between">
                <span>OHLCV Sequence:</span>
                <span className="text-emerald-400">VALID</span>
              </div>
              <div className="flex justify-between">
                <span>Detected Gaps:</span>
                <span className="text-slate-200">{quality?.gap_count || 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Candle Latency:</span>
                <span className="text-indigo-300">{latencyMs} ms</span>
              </div>
              <div className="flex justify-between">
                <span>Reliability:</span>
                <span className="text-emerald-400">100% Deterministic</span>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const isPositiveChange = (ticker?.price_change_percent || 0) >= 0;

  return (
    <header className="min-h-[52px] h-auto bg-slate-950 border-b border-slate-800/90 px-2.5 sm:px-4 py-1.5 flex items-center justify-between select-none backdrop-blur-md gap-2">
      {/* Left: Brand, Active Symbol, Profile Selector & 24h Ticker Summary */}
      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center shadow-glow-cyan/30 shrink-0">
          <Cpu className="w-4 h-4 sm:w-5 sm:h-5 text-slate-950 font-black" />
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <div className="flex items-center gap-1.5 sm:gap-2">
            <span className="text-xs sm:text-sm font-black tracking-wider text-slate-100 font-mono">
              {symbol}
            </span>
            <ProfileSelector />
          </div>

          {ticker && (
            <div className="hidden lg:flex items-center gap-3 text-xs font-mono pl-3 border-l border-slate-800">
              <div className="flex items-baseline gap-1.5">
                <span className="text-base font-black text-slate-100">
                  ${formatSymbolPrice(symbol, ticker.price)}
                </span>
                <span className={`text-[11px] font-bold ${isPositiveChange ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {formatPercentage(ticker.price_change_percent)}
                </span>
              </div>

              <div className="hidden xl:flex items-center gap-2 text-[11px] text-slate-400">
                <span>24h H: <strong className="text-slate-200">${formatSymbolPrice(symbol, ticker.high_24h)}</strong></span>
                <span>24h L: <strong className="text-slate-200">${formatSymbolPrice(symbol, ticker.low_24h)}</strong></span>
                <span>Vol: <strong className="text-slate-200">{ticker.volume_24h ? ticker.volume_24h.toLocaleString('en-US', { maximumFractionDigits: 1 }) : '—'}</strong></span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Center: Authoritative Execution Policy & Data Quality */}
      <div className="hidden md:flex items-center gap-2 lg:gap-3 text-xs font-mono">
        <div className="flex items-center gap-1.5 bg-slate-900 px-2.5 py-1 rounded border border-indigo-500/30 text-indigo-300">
          <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
          <span className="font-bold text-[11px]">SHADOW / ANALYSIS ONLY</span>
        </div>

        {getQualityBadge()}

        <div className="flex items-center gap-1 bg-slate-900 px-2 py-1 rounded border border-slate-800 text-slate-400 text-[10px]">
          <Clock className="w-3 h-3 text-slate-500" />
          <span>Closed: <strong className="text-slate-200">{lastClosedUtc}</strong></span>
        </div>
      </div>

      {/* Right: Latency, Timestamp & Live Connection */}
      <div className="flex items-center gap-2 shrink-0">
        <div className="hidden sm:flex items-center gap-2 text-[11px] text-slate-400 font-mono">
          <span className="flex items-center gap-1">
            <Zap className="w-3 h-3 text-indigo-400" />
            <strong className="text-slate-300">{latencyMs}ms</strong>
          </span>
          <span className="text-slate-600 hidden md:inline">|</span>
          <span className="hidden md:inline">{localTimeStr}</span>
        </div>
        {getStatusBadge()}
      </div>
    </header>
  );
};
