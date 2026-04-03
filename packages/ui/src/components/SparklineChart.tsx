export interface SparklineChartProps {
  data: number[];
  labels: string[];
  width?: number;
  height?: number;
}

export function SparklineChart({ data, labels, width = 600, height = 120 }: SparklineChartProps) {
  if (data.length === 0) return null;
  const points = data.map((v, i) => ({ x: i * (width / Math.max(data.length - 1, 1)), y: v }));
  const linePath = `M${points[0]!.x},${points[0]!.y} ` + points.slice(1).map((p, i) => {
    const prev = points[i]!;
    const cpx1 = prev.x + (p.x - prev.x) * 0.4;
    const cpx2 = prev.x + (p.x - prev.x) * 0.6;
    return `C${cpx1},${prev.y} ${cpx2},${p.y} ${p.x},${p.y}`;
  }).join(' ');
  const areaPath = `${linePath} L${points[points.length - 1]!.x},${height} L0,${height} Z`;
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ height: `${height}px` }}>
      <defs><linearGradient id="sparkline-grad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#8B5CF6" stopOpacity={0.3} /><stop offset="100%" stopColor="#8B5CF6" stopOpacity={0} /></linearGradient></defs>
      <path className="sparkline-area" fill="url(#sparkline-grad)" d={areaPath} />
      <path className="sparkline" d={linePath} />
      {points.map((p, i) => (<circle key={i} cx={p.x} cy={p.y} r={i === points.length - 1 ? 4 : 3} fill="#8B5CF6" stroke={i === points.length - 1 ? '#030303' : undefined} strokeWidth={i === points.length - 1 ? 2 : undefined} />))}
      {labels.map((label, i) => (<text key={i} x={points[i]?.x ?? 0} y={height - 5} fontFamily="Space Grotesk" fontSize={8} fill={i === labels.length - 1 ? 'rgba(196,181,253,0.9)' : 'rgba(138,138,142,0.6)'}>{label}</text>))}
    </svg>
  );
}
