import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export interface SparklineChartProps {
  data: number[];
  labels: string[];
  width?: number;
  height?: number;
}

export function SparklineChart({ data, labels, height = 120 }: SparklineChartProps) {
  if (data.length === 0) return null;

  // Transform data for Recharts
  const chartData = data.map((value, index) => ({
    date: labels[index] || '',
    records: value,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart
        data={chartData}
        margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
      >
        <defs>
          <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
        <XAxis
          dataKey="date"
          stroke="rgba(138,138,142,0.6)"
          style={{ fontSize: '10px', fontFamily: 'Space Grotesk' }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          stroke="rgba(138,138,142,0.6)"
          style={{ fontSize: '10px', fontFamily: 'Space Grotesk' }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value) => value.toLocaleString('zh-CN')}
        />
          <Tooltip
            content={({ active, payload, label }) => {
              if (!active || !payload || payload.length === 0) return null;
              const value = payload[0]?.value;
              if (value === undefined || value === null) return null;
              const numValue = typeof value === 'number' ? value : Number(value);
              
              return (
                <div
                  style={{
                    backgroundColor: '#1a1a1a',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    padding: '8px 12px',
                    fontSize: '12px',
                    animation: 'fadeIn 0.15s ease-out',
                  }}
                >
                  <div style={{ color: 'rgba(138,138,142,0.9)', marginBottom: '4px' }}>
                    {label}
                  </div>
                  <div style={{ color: '#C4B5FD', fontWeight: 600 }}>
                    {numValue.toLocaleString('zh-CN')} 条记录
                  </div>
                </div>
              );
            }}
            cursor={{ stroke: '#8B5CF6', strokeWidth: 1, strokeDasharray: '5 5' }}
            animationDuration={0}
            isAnimationActive={false}
          />
        <Area
          type="monotone"
          dataKey="records"
          stroke="#8B5CF6"
          strokeWidth={2}
          fill="url(#colorValue)"
          dot={{
            fill: '#8B5CF6',
            strokeWidth: 2,
            r: 3,
            stroke: '#030303',
          }}
          activeDot={{
            r: 6,
            fill: '#8B5CF6',
            stroke: '#030303',
            strokeWidth: 2,
          }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
