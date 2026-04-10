import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

export interface DonutChartProps {
  percentage: number;
  label: string;
  sublabel?: string;
}

export function DonutChart({ percentage, label, sublabel }: DonutChartProps) {
  const data = [
    { name: '已使用', value: percentage, color: '#8B5CF6' },
    { name: '剩余', value: 100 - percentage, color: 'rgba(255,255,255,0.06)' },
  ];

  return (
    <div className="flex flex-col items-center">
      <ResponsiveContainer width={140} height={140}>
        <PieChart style={{ outline: 'none' }}>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={45}
            outerRadius={60}
            startAngle={90}
            endAngle={-270}
            dataKey="value"
            stroke="none"
            style={{ outline: 'none' }}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.color}
                style={
                  index === 0
                    ? { filter: 'drop-shadow(0 0 6px rgba(139,92,246,0.5))', outline: 'none' }
                    : { outline: 'none' }
                }
              />
            ))}
          </Pie>
          <Tooltip
            content={({ active, payload }) => {
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
                  <div style={{ color: '#C4B5FD', fontWeight: 600 }}>
                    {numValue.toFixed(1)}%
                  </div>
                </div>
              );
            }}
            animationDuration={0}
            isAnimationActive={false}
          />
          <text
            x="50%"
            y="45%"
            textAnchor="middle"
            dominantBaseline="middle"
            style={{
              fontFamily: 'Space Grotesk',
              fontSize: '18px',
              fill: '#F5F5F7',
              fontWeight: 500,
              pointerEvents: 'none',
            }}
          >
            {label}
          </text>
          {sublabel && (
            <text
              x="50%"
              y="58%"
              textAnchor="middle"
              dominantBaseline="middle"
              style={{
                fontFamily: 'Inter',
                fontSize: '8px',
                fill: 'rgba(138,138,142,0.8)',
                pointerEvents: 'none',
              }}
            >
              {sublabel}
            </text>
          )}
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
