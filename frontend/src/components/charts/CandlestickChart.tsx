'use client';

import { useEffect, useRef } from 'react';
import { createChart, CandlestickSeries, type IChartApi, type CandlestickData, type Time, ColorType } from 'lightweight-charts';

interface CandlestickChartProps {
  data: { time: string; open: number; high: number; low: number; close: number }[];
  targetPrice?: number;
  stopLoss?: number;
  height?: number;
}

export function CandlestickChart({ data, targetPrice, stopLoss, height = 300 }: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current || data.length < 2) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#9CA3AF',
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: 10,
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.03)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.03)' },
      },
      crosshair: {
        vertLine: { color: '#6366F1', width: 1, style: 2 },
        horzLine: { color: '#6366F1', width: 1, style: 2 },
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.06)',
        timeVisible: true,
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.06)',
      },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#00E676',
      downColor: '#FF5252',
      borderUpColor: '#00E676',
      borderDownColor: '#FF5252',
      wickUpColor: '#00E676',
      wickDownColor: '#FF5252',
    });

    const formattedData: CandlestickData<Time>[] = data.map((d) => ({
      time: d.time as Time,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));

    candleSeries.setData(formattedData);

    // Add target price line
    if (targetPrice) {
      candleSeries.createPriceLine({
        price: targetPrice,
        color: '#00E676',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: 'Target',
      });
    }

    // Add stop-loss line
    if (stopLoss) {
      candleSeries.createPriceLine({
        price: stopLoss,
        color: '#FF5252',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: 'Stop',
      });
    }

    chart.timeScale().fitContent();
    chartRef.current = chart;

    // Handle resize
    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
      chartRef.current = null;
    };
  }, [data, targetPrice, stopLoss, height]);

  if (data.length < 2) {
    return (
      <div className="text-center py-8 text-xs text-text-muted">
        Not enough data for candlestick chart
      </div>
    );
  }

  return <div ref={containerRef} className="w-full" />;
}
