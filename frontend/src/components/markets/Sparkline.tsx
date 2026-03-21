interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  positive?: boolean;
  target?: number;
  stopLoss?: number;
  responsive?: boolean;
}

export function Sparkline({ data, width = 60, height = 20, positive = true, target, stopLoss, responsive = false }: SparklineProps) {
  if (data.length < 2) return null;

  // Include target and stop-loss in min/max calculation so lines are visible
  const allValues = [...data, ...(target != null ? [target] : []), ...(stopLoss != null ? [stopLoss] : [])];
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const range = max - min || 1;

  const toY = (val: number) => height - ((val - min) / range) * height;

  const points = data
    .map((val, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = toY(val);
      return `${x},${y}`;
    })
    .join(' ');

  const color = positive ? '#00E676' : '#FF5252';

  return (
    <svg
      {...(responsive
        ? { viewBox: `0 0 ${width} ${height}`, className: 'w-full h-auto', preserveAspectRatio: 'none' }
        : { width, height, className: 'inline-block' }
      )}
    >
      {/* Target reference line */}
      {target != null && (
        <line
          x1={0} y1={toY(target)} x2={width} y2={toY(target)}
          stroke="#00E676" strokeWidth={0.5} strokeDasharray="2,2" opacity={0.6}
        />
      )}
      {/* Stop-loss reference line */}
      {stopLoss != null && (
        <line
          x1={0} y1={toY(stopLoss)} x2={width} y2={toY(stopLoss)}
          stroke="#FF5252" strokeWidth={0.5} strokeDasharray="2,2" opacity={0.6}
        />
      )}
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
