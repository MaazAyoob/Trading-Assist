import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  createChart,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  IChartApi,
  ISeriesApi,
  CandlestickData,
  HistogramData,
  LineData,
  UTCTimestamp,
  ColorType,
  CrosshairMode,
  IPriceLine,
  createSeriesMarkers,
  ISeriesMarkersPluginApi,
  SeriesMarker,
  Time,
} from 'lightweight-charts';
import { useMarketStore } from '../../stores/marketStore';
import { TimeframeSelector } from './TimeframeSelector';
import { RefreshCw, ZoomIn, ZoomOut, Maximize2, Layers } from 'lucide-react';

const DEFAULT_BAR_SPACING = 6;

export const TradingViewChart: React.FC = () => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const markersPluginRef = useRef<ISeriesMarkersPluginApi<Time> | null>(null);

  // Track if chart has performed initial fit
  const hasFittedRef = useRef<boolean>(false);

  // Overlay Series Refs
  const ema9SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema21SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema50SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema200SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const vwapSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbUpperSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbMiddleSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbLowerSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const supertrendSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  // Price Lines Refs for Structure (Swings, BOS, Zones)
  const priceLinesRef = useRef<IPriceLine[]>([]);

  const {
    candles,
    symbol,
    timeframe,
    isLoading,
    indicatorHistory,
    confirmedStructure,
    signalHistory,
    confirmedSignal,
    confirmedTradeDecision,
    realtimeTradeDecision,
    chartOverlays,
    cleanChart,
    toggleCleanChart,
    toggleOverlay,
    loadHistoricalData,
  } = useMarketStore();

  const [hoveredCandle, setHoveredCandle] = useState<{
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    time: string;
  } | null>(null);

  const [barSpacing, setBarSpacing] = useState<number>(() => {
    if (typeof window !== 'undefined') {
      const saved = sessionStorage.getItem('trading_chart_bar_spacing');
      if (saved) {
        const val = parseFloat(saved);
        if (!isNaN(val) && val >= 1 && val <= 50) return val;
      }
    }
    return DEFAULT_BAR_SPACING;
  });

  const [showMobileOverlays, setShowMobileOverlays] = useState<boolean>(false);

  // Candle Zoom Controls
  const handleZoomIn = useCallback(() => {
    if (!chartRef.current) return;
    const newSpacing = Math.min(48, Math.round(barSpacing * 1.3));
    chartRef.current.timeScale().applyOptions({ barSpacing: newSpacing });
    setBarSpacing(newSpacing);
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('trading_chart_bar_spacing', String(newSpacing));
    }
  }, [barSpacing]);

  const handleZoomOut = useCallback(() => {
    if (!chartRef.current) return;
    const newSpacing = Math.max(1.5, Math.round(barSpacing * 0.75 * 10) / 10);
    chartRef.current.timeScale().applyOptions({ barSpacing: newSpacing });
    setBarSpacing(newSpacing);
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('trading_chart_bar_spacing', String(newSpacing));
    }
  }, [barSpacing]);

  const handleFitContent = useCallback(() => {
    if (!chartRef.current) return;
    chartRef.current.timeScale().fitContent();
    const defaultSpacing = DEFAULT_BAR_SPACING;
    chartRef.current.timeScale().applyOptions({ barSpacing: defaultSpacing });
    setBarSpacing(defaultSpacing);
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('trading_chart_bar_spacing', String(defaultSpacing));
    }
  }, []);

  const handleSetDensity = useCallback((spacing: number) => {
    if (!chartRef.current) return;
    chartRef.current.timeScale().applyOptions({ barSpacing: spacing });
    setBarSpacing(spacing);
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('trading_chart_bar_spacing', String(spacing));
    }
  }, []);

  // Initialize TradingView Chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const container = chartContainerRef.current;
    const initialWidth = container.clientWidth || 320;
    const initialHeight = container.clientHeight || 340;

    const chart = createChart(container, {
      width: initialWidth,
      height: initialHeight,
      layout: {
        background: { type: ColorType.Solid, color: '#0a0d14' },
        textColor: '#94a3b8',
        fontSize: 11,
        fontFamily: 'JetBrains Mono, monospace',
      },
      grid: {
        vertLines: { color: 'rgba(31, 41, 61, 0.4)' },
        horzLines: { color: 'rgba(31, 41, 61, 0.4)' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: '#00e5ff',
          width: 1,
          style: 3,
          labelBackgroundColor: '#161c2b',
        },
        horzLine: {
          color: '#00e5ff',
          width: 1,
          style: 3,
          labelBackgroundColor: '#161c2b',
        },
      },
      rightPriceScale: {
        borderColor: '#1f293d',
        scaleMargins: {
          top: 0.08,
          bottom: 0.2,
        },
      },
      timeScale: {
        borderColor: '#1f293d',
        timeVisible: true,
        secondsVisible: false,
        barSpacing: barSpacing,
        minBarSpacing: 1,
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: false, // Critical: Allows vertical page scrolling on mobile
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true, // Pinch-to-zoom on touch devices
      },
    });

    // Main Candlestick Series
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#00e676',
      downColor: '#ff3b30',
      borderUpColor: '#00e676',
      borderDownColor: '#ff3b30',
      wickUpColor: '#00e676',
      wickDownColor: '#ff3b30',
    });

    // Initialize Markers Plugin
    markersPluginRef.current = createSeriesMarkers(candleSeries, []);

    // Volume Histogram Series
    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '', // overlay
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    // Overlay Lines
    ema9SeriesRef.current = chart.addSeries(LineSeries, { color: '#00e5ff', lineWidth: 1, title: 'EMA 9' });
    ema21SeriesRef.current = chart.addSeries(LineSeries, { color: '#ffd600', lineWidth: 1, title: 'EMA 21' });
    ema50SeriesRef.current = chart.addSeries(LineSeries, { color: '#c084fc', lineWidth: 1, title: 'EMA 50' });
    ema200SeriesRef.current = chart.addSeries(LineSeries, { color: '#f43f5e', lineWidth: 2, title: 'EMA 200' });
    vwapSeriesRef.current = chart.addSeries(LineSeries, { color: '#f59e0b', lineWidth: 1, lineStyle: 2, title: 'VWAP' });

    bbUpperSeriesRef.current = chart.addSeries(LineSeries, { color: 'rgba(0, 229, 255, 0.5)', lineWidth: 1, lineStyle: 2 });
    bbMiddleSeriesRef.current = chart.addSeries(LineSeries, { color: 'rgba(255, 255, 255, 0.3)', lineWidth: 1 });
    bbLowerSeriesRef.current = chart.addSeries(LineSeries, { color: 'rgba(0, 229, 255, 0.5)', lineWidth: 1, lineStyle: 2 });

    supertrendSeriesRef.current = chart.addSeries(LineSeries, { color: '#10b981', lineWidth: 2, title: 'Supertrend' });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;

    // Crosshair move handler
    chart.subscribeCrosshairMove((param) => {
      if (!param.time || !param.seriesData.get(candleSeries)) {
        setHoveredCandle(null);
        return;
      }

      const data = param.seriesData.get(candleSeries) as any;
      const volData = param.seriesData.get(volumeSeries) as any;
      if (data) {
        setHoveredCandle({
          open: data.open,
          high: data.high,
          low: data.low,
          close: data.close,
          volume: volData?.value || 0,
          time: new Date((param.time as number) * 1000).toUTCString(),
        });
      }
    });

    const resizeObserver = new ResizeObserver((entries) => {
      if (entries.length === 0 || !entries[0].contentRect) return;
      const { width, height } = entries[0].contentRect;
      if (width > 0 && height > 0) {
        chart.applyOptions({ width, height });
        if (!hasFittedRef.current && candleSeriesRef.current) {
          hasFittedRef.current = true;
          chart.timeScale().fitContent();
        }
      }
    });

    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
      markersPluginRef.current = null;
      ema9SeriesRef.current = null;
      ema21SeriesRef.current = null;
      ema50SeriesRef.current = null;
      ema200SeriesRef.current = null;
      vwapSeriesRef.current = null;
      bbUpperSeriesRef.current = null;
      bbMiddleSeriesRef.current = null;
      bbLowerSeriesRef.current = null;
      supertrendSeriesRef.current = null;
      hasFittedRef.current = false;
    };
  }, []);

  // Update Candles and Volume
  useEffect(() => {
    if (!candleSeriesRef.current || !volumeSeriesRef.current || candles.length === 0) return;

    const validCandles = candles
      .filter((c) => c && c.timestamp && !isNaN(c.open) && !isNaN(c.high) && !isNaN(c.low) && !isNaN(c.close))
      .map((c) => ({
        time: Math.floor(c.timestamp / 1000) as UTCTimestamp,
        open: Number(c.open),
        high: Math.max(Number(c.high), Number(c.open), Number(c.close)),
        low: Math.min(Number(c.low), Number(c.open), Number(c.close)),
        close: Number(c.close),
        volume: Number(c.volume) || 0,
      }))
      .sort((a, b) => (a.time as number) - (b.time as number));

    const uniqueCandles: CandlestickData[] = [];
    const formattedVolume: HistogramData[] = [];
    const seenTimes = new Set<number>();

    for (const c of validCandles) {
      const t = c.time as number;
      if (!seenTimes.has(t)) {
        seenTimes.add(t);
        uniqueCandles.push({
          time: c.time,
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        });
        formattedVolume.push({
          time: c.time,
          value: c.volume,
          color: c.close >= c.open ? 'rgba(0, 230, 118, 0.4)' : 'rgba(255, 59, 48, 0.4)',
        });
      }
    }

    if (uniqueCandles.length > 0) {
      candleSeriesRef.current.setData(uniqueCandles);
      volumeSeriesRef.current.setData(formattedVolume);

      if (chartRef.current && !hasFittedRef.current) {
        hasFittedRef.current = true;
        chartRef.current.timeScale().fitContent();
        chartRef.current.timeScale().applyOptions({ barSpacing });
      }
    }
  }, [candles]);

  // Update Overlay Indicator Series
  useEffect(() => {
    if (indicatorHistory.length === 0) return;

    const extractLineData = (extractor: (p: any) => number | null | undefined): LineData[] => {
      const res: LineData[] = [];
      for (const p of indicatorHistory) {
        const val = extractor(p);
        if (val != null) {
          res.push({
            time: Math.floor(p.timestamp / 1000) as UTCTimestamp,
            value: val,
          });
        }
      }
      return res;
    };

    if (ema9SeriesRef.current) {
      const show = !cleanChart && chartOverlays.ema9;
      ema9SeriesRef.current.applyOptions({ visible: show });
      ema9SeriesRef.current.setData(show ? extractLineData((p) => p.ema_9) : []);
    }

    if (ema21SeriesRef.current) {
      const show = !cleanChart && chartOverlays.ema21;
      ema21SeriesRef.current.applyOptions({ visible: show });
      ema21SeriesRef.current.setData(show ? extractLineData((p) => p.ema_21) : []);
    }

    if (ema50SeriesRef.current) {
      const show = !cleanChart && chartOverlays.ema50;
      ema50SeriesRef.current.applyOptions({ visible: show });
      ema50SeriesRef.current.setData(show ? extractLineData((p) => p.ema_50) : []);
    }

    if (ema200SeriesRef.current) {
      const show = !cleanChart && chartOverlays.ema200;
      ema200SeriesRef.current.applyOptions({ visible: show });
      ema200SeriesRef.current.setData(show ? extractLineData((p) => p.ema_200) : []);
    }

    if (vwapSeriesRef.current) {
      const show = !cleanChart && chartOverlays.vwap;
      vwapSeriesRef.current.applyOptions({ visible: show });
      vwapSeriesRef.current.setData(show ? extractLineData((p) => p.vwap) : []);
    }

    if (bbUpperSeriesRef.current && bbMiddleSeriesRef.current && bbLowerSeriesRef.current) {
      const show = !cleanChart && chartOverlays.bollinger;
      bbUpperSeriesRef.current.applyOptions({ visible: show });
      bbMiddleSeriesRef.current.applyOptions({ visible: show });
      bbLowerSeriesRef.current.applyOptions({ visible: show });
      bbUpperSeriesRef.current.setData(show ? extractLineData((p) => p.bb_upper) : []);
      bbMiddleSeriesRef.current.setData(show ? extractLineData((p) => p.bb_middle) : []);
      bbLowerSeriesRef.current.setData(show ? extractLineData((p) => p.bb_lower) : []);
    }

    if (supertrendSeriesRef.current) {
      const show = !cleanChart && chartOverlays.supertrend;
      supertrendSeriesRef.current.applyOptions({ visible: show });
      supertrendSeriesRef.current.setData(show ? extractLineData((p) => p.supertrend) : []);
    }
  }, [indicatorHistory, chartOverlays, cleanChart]);

  // Update Price Lines for Structure Overlays (Swings, BOS, S&R Zones)
  useEffect(() => {
    if (!candleSeriesRef.current) return;

    // Clear existing structure price lines
    priceLinesRef.current.forEach((pl) => {
      try {
        candleSeriesRef.current?.removePriceLine(pl);
      } catch (e) {}
    });
    priceLinesRef.current = [];

    if (!confirmedStructure) return;

    // 1. Swings Overlay (Active Structural High & Low)
    if (!cleanChart && chartOverlays.swings) {
      if (confirmedStructure.active_structural_high) {
        const shLine = candleSeriesRef.current.createPriceLine({
          price: confirmedStructure.active_structural_high.price,
          color: '#10b981',
          lineWidth: 1,
          lineStyle: 1, // Dotted
          axisLabelVisible: true,
          title: 'STR-HIGH',
        });
        priceLinesRef.current.push(shLine);
      }
      if (confirmedStructure.active_structural_low) {
        const slLine = candleSeriesRef.current.createPriceLine({
          price: confirmedStructure.active_structural_low.price,
          color: '#f43f5e',
          lineWidth: 1,
          lineStyle: 1,
          axisLabelVisible: true,
          title: 'STR-LOW',
        });
        priceLinesRef.current.push(slLine);
      }
    }

    // 2. Support / Resistance Zones Overlay
    if (!cleanChart && chartOverlays.zones) {
      confirmedStructure.resistance_zones.slice(0, 2).forEach((rz) => {
        const resLine = candleSeriesRef.current?.createPriceLine({
          price: rz.price_center,
          color: 'rgba(244, 63, 94, 0.7)',
          lineWidth: 1,
          lineStyle: 2, // Dashed
          axisLabelVisible: true,
          title: `RES (${rz.touch_count})`,
        });
        if (resLine) priceLinesRef.current.push(resLine);
      });

      confirmedStructure.support_zones.slice(0, 2).forEach((sz) => {
        const supLine = candleSeriesRef.current?.createPriceLine({
          price: sz.price_center,
          color: 'rgba(16, 185, 129, 0.7)',
          lineWidth: 1,
          lineStyle: 2,
          axisLabelVisible: true,
          title: `SUP (${sz.touch_count})`,
        });
        if (supLine) priceLinesRef.current.push(supLine);
      });
    }

    // Phase 10: Trade Plan Price Lines (Entry Zone, Stop Loss, TP1, TP2, TP3)
    const activePlan = confirmedTradeDecision || realtimeTradeDecision;
    if (chartOverlays.tradePlan && activePlan && (activePlan.decision === 'BUY' || activePlan.decision === 'SELL')) {
      // 1. Entry Level
      if (activePlan.entry) {
        const entryLine = candleSeriesRef.current?.createPriceLine({
          price: activePlan.entry.planned_entry_price,
          color: '#38bdf8', // Sky blue
          lineWidth: 2,
          lineStyle: 0, // Solid
          axisLabelVisible: true,
          title: `ENTRY ($${activePlan.entry.planned_entry_price.toLocaleString('en-US')})`,
        });
        if (entryLine) priceLinesRef.current.push(entryLine);

        // Entry Zone bounds
        if (activePlan.entry.entry_zone_low !== activePlan.entry.planned_entry_price) {
          const zoneLowLine = candleSeriesRef.current?.createPriceLine({
            price: activePlan.entry.entry_zone_low,
            color: 'rgba(56, 189, 248, 0.4)',
            lineWidth: 1,
            lineStyle: 3, // Dotted
            axisLabelVisible: false,
            title: 'Zone Low',
          });
          if (zoneLowLine) priceLinesRef.current.push(zoneLowLine);
        }
        if (activePlan.entry.entry_zone_high !== activePlan.entry.planned_entry_price) {
          const zoneHighLine = candleSeriesRef.current?.createPriceLine({
            price: activePlan.entry.entry_zone_high,
            color: 'rgba(56, 189, 248, 0.4)',
            lineWidth: 1,
            lineStyle: 3, // Dotted
            axisLabelVisible: false,
            title: 'Zone High',
          });
          if (zoneHighLine) priceLinesRef.current.push(zoneHighLine);
        }
      }

      // 2. Stop Loss Level
      if (activePlan.stop_loss) {
        const slLine = candleSeriesRef.current?.createPriceLine({
          price: activePlan.stop_loss.price,
          color: '#f43f5e', // Rose
          lineWidth: 2,
          lineStyle: 2, // Dashed
          axisLabelVisible: true,
          title: `STOP ($${activePlan.stop_loss.price.toLocaleString('en-US')})`,
        });
        if (slLine) priceLinesRef.current.push(slLine);
      }

      // 3. Take Profit Levels
      if (activePlan.take_profits) {
        const tp1Line = candleSeriesRef.current?.createPriceLine({
          price: activePlan.take_profits.tp1.adjusted_target,
          color: '#10b981', // Emerald
          lineWidth: 2,
          lineStyle: 2,
          axisLabelVisible: true,
          title: `TP1: $${activePlan.take_profits.tp1.adjusted_target.toLocaleString('en-US')} (${activePlan.take_profits.tp1.actual_rr_after_adjustment.toFixed(2)}R)`,
        });
        if (tp1Line) priceLinesRef.current.push(tp1Line);

        const tp2Line = candleSeriesRef.current?.createPriceLine({
          price: activePlan.take_profits.tp2.adjusted_target,
          color: '#059669', // Darker Emerald
          lineWidth: 1,
          lineStyle: 2,
          axisLabelVisible: true,
          title: `TP2: $${activePlan.take_profits.tp2.adjusted_target.toLocaleString('en-US')} (${activePlan.take_profits.tp2.actual_rr_after_adjustment.toFixed(2)}R)`,
        });
        if (tp2Line) priceLinesRef.current.push(tp2Line);

        const tp3Line = candleSeriesRef.current?.createPriceLine({
          price: activePlan.take_profits.tp3.adjusted_target,
          color: '#047857',
          lineWidth: 1,
          lineStyle: 2,
          axisLabelVisible: true,
          title: `TP3: $${activePlan.take_profits.tp3.adjusted_target.toLocaleString('en-US')} (${activePlan.take_profits.tp3.actual_rr_after_adjustment.toFixed(2)}R)`,
        });
        if (tp3Line) priceLinesRef.current.push(tp3Line);
      }
    }
  }, [confirmedStructure, confirmedTradeDecision, realtimeTradeDecision, chartOverlays]);

  // Update Signal Markers on Candlestick Series using Markers Plugin
  useEffect(() => {
    if (!markersPluginRef.current) return;

    if (!chartOverlays.signalMarkers) {
      markersPluginRef.current.setMarkers([]);
      return;
    }

    const markers: SeriesMarker<UTCTimestamp>[] = [];

    // Combine historical signal records and latest confirmed signal
    const allSignals = [...signalHistory];
    if (confirmedSignal && !allSignals.some((s) => s.timestamp === confirmedSignal.timestamp)) {
      allSignals.push(confirmedSignal);
    }

    const seenMarkerTimes = new Set<number>();
    const sortedSignals = allSignals
      .filter((s) => s && s.timestamp && (s.direction === 'LONG_SETUP' || s.direction === 'SHORT_SETUP'))
      .sort((a, b) => a.timestamp - b.timestamp);

    sortedSignals.forEach((sig) => {
      const time = Math.floor(sig.timestamp / 1000) as UTCTimestamp;
      if (seenMarkerTimes.has(time as number)) return;
      seenMarkerTimes.add(time as number);

      if (sig.direction === 'LONG_SETUP') {
        markers.push({
          time,
          position: 'belowBar',
          color: '#10b981',
          shape: 'arrowUp',
          text: `▲ ${Math.round(sig.score)}`,
        });
      } else if (sig.direction === 'SHORT_SETUP') {
        markers.push({
          time,
          position: 'aboveBar',
          color: '#f43f5e',
          shape: 'arrowDown',
          text: `▼ ${Math.abs(Math.round(sig.score))}`,
        });
      }
    });

    markersPluginRef.current.setMarkers(markers);
  }, [signalHistory, confirmedSignal, chartOverlays.signalMarkers]);

  const latestCandle = candles.length > 0 ? candles[candles.length - 1] : null;
  const displayData = hoveredCandle || (latestCandle ? {
    open: latestCandle.open,
    high: latestCandle.high,
    low: latestCandle.low,
    close: latestCandle.close,
    volume: latestCandle.volume,
    time: new Date(latestCandle.timestamp).toUTCString(),
  } : null);

  return (
    <div className="flex-1 flex flex-col bg-surface-card rounded-xl border border-border overflow-hidden relative shadow-xl">
      {/* Chart Top Action Bar: Timeframe Selector & Overlay Toggles */}
      <div className="min-h-[44px] h-auto py-1 px-2 sm:px-3 bg-surface flex flex-wrap items-center justify-between border-b border-border/80 z-10 select-none gap-1.5 sm:gap-2">
        <div className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto scrollbar-none max-w-full py-0.5">
          <TimeframeSelector />

          <button
            onClick={() => setShowMobileOverlays(!showMobileOverlays)}
            className={`sm:hidden p-1.5 rounded border transition flex items-center gap-1 text-[11px] font-mono shrink-0 ${
              showMobileOverlays
                ? 'bg-indigo-600 text-white border-indigo-500'
                : 'bg-surface-elevated/60 border-border-subtle text-text-muted hover:text-text-primary'
            }`}
            title="Toggle Technical Overlays"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Overlays</span>
          </button>
          
          {/* Interactive Overlay Toggles — Always visible on sm+, expandable on mobile */}
          <div className={`${showMobileOverlays ? 'flex' : 'hidden sm:flex'} items-center gap-1 text-[10px] sm:text-[11px] font-mono shrink-0 overflow-x-auto scrollbar-none`}>
            <button
              onClick={() => toggleOverlay('ema9')}
              className={`px-2 py-1 rounded border transition shrink-0 ${
                chartOverlays.ema9
                  ? 'bg-accent-cyan/20 border-accent-cyan text-accent-cyan font-bold'
                  : 'bg-surface-elevated/40 border-border-subtle text-text-muted hover:text-text-secondary'
              }`}
            >
              EMA 9
            </button>

            <button
              onClick={() => toggleOverlay('ema21')}
              className={`px-2 py-1 rounded border transition shrink-0 ${
                chartOverlays.ema21
                  ? 'bg-accent-gold/20 border-accent-gold text-accent-gold font-bold'
                  : 'bg-surface-elevated/40 border-border-subtle text-text-muted hover:text-text-secondary'
              }`}
            >
              EMA 21
            </button>

            <button
              onClick={() => toggleOverlay('vwap')}
              className={`px-2 py-1 rounded border transition shrink-0 ${
                chartOverlays.vwap
                  ? 'bg-amber-500/20 border-amber-400 text-amber-300 font-bold'
                  : 'bg-surface-elevated/40 border-border-subtle text-text-muted hover:text-text-secondary'
              }`}
            >
              VWAP
            </button>

            <button
              onClick={() => toggleOverlay('bollinger')}
              className={`px-2 py-1 rounded border transition shrink-0 ${
                chartOverlays.bollinger
                  ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 font-bold'
                  : 'bg-surface-elevated/40 border-border-subtle text-text-muted hover:text-text-secondary'
              }`}
            >
              BB
            </button>

            <button
              onClick={() => toggleOverlay('supertrend')}
              className={`px-2 py-1 rounded border transition shrink-0 ${
                chartOverlays.supertrend
                  ? 'bg-emerald-500/20 border-emerald-400 text-emerald-300 font-bold'
                  : 'bg-surface-elevated/40 border-border-subtle text-text-muted hover:text-text-secondary'
              }`}
            >
              Supertrend
            </button>

            <span className="text-border-subtle mx-0.5">|</span>

            {/* Structure Overlays */}
            <button
              onClick={() => toggleOverlay('swings')}
              className={`px-2 py-1 rounded border transition shrink-0 ${
                chartOverlays.swings
                  ? 'bg-purple-500/20 border-purple-400 text-purple-300 font-bold'
                  : 'bg-surface-elevated/40 border-border-subtle text-text-muted hover:text-text-secondary'
              }`}
            >
              Swings
            </button>

            <button
              onClick={() => toggleOverlay('zones')}
              className={`px-2 py-1 rounded border transition shrink-0 ${
                chartOverlays.zones
                  ? 'bg-rose-500/20 border-rose-400 text-rose-300 font-bold'
                  : 'bg-surface-elevated/40 border-border-subtle text-text-muted hover:text-text-secondary'
              }`}
            >
              S&R Zones
            </button>

            <span className="text-border-subtle mx-0.5">|</span>

            {/* Signal Markers Toggle */}
            <button
              onClick={() => toggleOverlay('signalMarkers')}
              className={`px-2 py-1 rounded border transition shrink-0 ${
                chartOverlays.signalMarkers
                  ? 'bg-purple-500/20 border-purple-400 text-purple-300 font-bold'
                  : 'bg-surface-elevated/40 border-border-subtle text-text-muted hover:text-text-secondary'
              }`}
            >
              Signals (▲/▼)
            </button>

            {/* Phase 10: Trade Plan SL/TP Toggle */}
            <button
              onClick={() => toggleOverlay('tradePlan')}
              className={`px-2 py-1 rounded border transition shrink-0 ${
                chartOverlays.tradePlan
                  ? 'bg-indigo-600/30 border-indigo-400 text-indigo-200 font-bold shadow-lg shadow-indigo-500/20'
                  : 'bg-surface-elevated/40 border-border-subtle text-text-muted hover:text-text-secondary'
              }`}
            >
              Trade Plan
            </button>

            <span className="text-border-subtle mx-0.5">|</span>

            {/* Clean Chart Mode Toggle */}
            <button
              onClick={toggleCleanChart}
              className={`px-2 py-1 rounded border transition shrink-0 ${
                cleanChart
                  ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 font-bold'
                  : 'bg-surface-elevated/40 border-border-subtle text-text-muted hover:text-text-secondary'
              }`}
              title="Hide secondary technical lines to focus on Price & Trade Plan"
            >
              Clean
            </button>
          </div>
        </div>

        {/* Reload button */}
        <div className="flex items-center gap-1.5 shrink-0 ml-auto">
          <button
            onClick={() => loadHistoricalData()}
            disabled={isLoading}
            title="Reload Market, Indicators & Signals"
            className="p-2 rounded-lg bg-surface-elevated/60 hover:bg-surface-elevated border border-border-subtle text-text-secondary hover:text-text-primary transition min-w-[36px] min-h-[36px] flex items-center justify-center"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-accent-cyan' : ''}`} />
          </button>
        </div>
      </div>

      {/* OHLCV Legend Bar & Visual Candle Zoom Controls */}
      <div className="bg-surface/90 backdrop-blur-sm px-2.5 sm:px-3 py-1.5 border-b border-border/40 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono select-none z-10">
        {/* Left: OHLCV Values */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <span className="text-accent-cyan font-black">{symbol}</span>
          {displayData ? (
            <>
              <div>
                <span className="text-text-muted">O: </span>
                <span className="text-text-primary">${displayData.open.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
              </div>
              <div>
                <span className="text-text-muted">H: </span>
                <span className="text-emerald-400">${displayData.high.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
              </div>
              <div>
                <span className="text-text-muted">L: </span>
                <span className="text-rose-400">${displayData.low.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
              </div>
              <div>
                <span className="text-text-muted">C: </span>
                <span className={displayData.close >= displayData.open ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                  ${displayData.close.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="hidden xs:inline">
                <span className="text-text-muted">Vol: </span>
                <span className="text-text-secondary">{displayData.volume.toFixed(2)}</span>
              </div>
            </>
          ) : (
            <span className="text-text-muted">Awaiting stream...</span>
          )}
        </div>

        {/* Right: Candle Size & Visual Zoom Controls (Toolbar) */}
        <div className="flex items-center gap-1 shrink-0 ml-auto bg-slate-950/80 p-0.5 rounded-lg border border-slate-800">
          <span className="text-[9px] text-slate-500 font-bold px-1 hidden md:inline uppercase">Candle Size:</span>
          
          <button
            onClick={handleZoomIn}
            className="p-1 sm:px-1.5 sm:py-0.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition flex items-center gap-0.5 text-[10px]"
            title="Zoom In / Larger Candles (+)"
            aria-label="Zoom In Candles"
          >
            <ZoomIn className="w-3.5 h-3.5 text-indigo-400" />
            <span className="hidden xs:inline">+</span>
          </button>

          <button
            onClick={handleZoomOut}
            className="p-1 sm:px-1.5 sm:py-0.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition flex items-center gap-0.5 text-[10px]"
            title="Zoom Out / Smaller Candles (-)"
            aria-label="Zoom Out Candles"
          >
            <ZoomOut className="w-3.5 h-3.5 text-indigo-400" />
            <span className="hidden xs:inline">-</span>
          </button>

          <button
            onClick={handleFitContent}
            className="px-1.5 py-0.5 rounded bg-indigo-950/60 border border-indigo-800/60 text-indigo-300 hover:bg-indigo-900/80 transition flex items-center gap-1 text-[10px] font-bold"
            title="Reset Zoom / Fit All Candles"
          >
            <Maximize2 className="w-3 h-3" />
            <span>Fit</span>
          </button>

          {/* Quick Density Presets */}
          <div className="hidden sm:flex items-center gap-0.5 pl-1 border-l border-slate-800">
            <button
              onClick={() => handleSetDensity(3)}
              className={`px-1.5 py-0.5 rounded text-[9px] font-mono transition ${
                barSpacing <= 4
                  ? 'bg-indigo-600 text-white font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Dense Candle Spacing (3px)"
            >
              Dense
            </button>
            <button
              onClick={() => handleSetDensity(6)}
              className={`px-1.5 py-0.5 rounded text-[9px] font-mono transition ${
                barSpacing > 4 && barSpacing < 10
                  ? 'bg-indigo-600 text-white font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Standard Candle Spacing (6px)"
            >
              Std
            </button>
            <button
              onClick={() => handleSetDensity(14)}
              className={`px-1.5 py-0.5 rounded text-[9px] font-mono transition ${
                barSpacing >= 10
                  ? 'bg-indigo-600 text-white font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Wide Candle Spacing (14px)"
            >
              Wide
            </button>
          </div>
        </div>
      </div>

      {/* Chart Canvas: Explicit Responsive Heights (320px on phones, 420px on tablet, 520px on desktop) */}
      <div className="w-full h-[320px] sm:h-[420px] lg:h-[520px] min-h-[300px] relative bg-background">
        {isLoading && candles.length === 0 && (
          <div className="absolute inset-0 bg-background/85 backdrop-blur-sm z-20 flex flex-col items-center justify-center gap-3">
            <div className="w-8 h-8 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin"></div>
            <span className="text-xs font-mono text-text-secondary">Loading {symbol} {timeframe} market candles...</span>
          </div>
        )}

        {!isLoading && candles.length === 0 && (
          <div className="absolute inset-0 bg-background z-20 flex flex-col items-center justify-center gap-3 p-4 text-center">
            <span className="text-xs font-mono text-slate-400">No candle data received for {symbol} ({timeframe}).</span>
            <button
              onClick={() => loadHistoricalData()}
              className="px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-mono text-xs font-bold shadow-lg shadow-indigo-600/30 flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Load</span>
            </button>
          </div>
        )}

        <div ref={chartContainerRef} className="w-full h-full touch-pan-y" />
      </div>
    </div>
  );
};
