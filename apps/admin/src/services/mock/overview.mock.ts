export interface KpiItem {
  label: string;
  value: string;
  accentColor?: string;
  trend?: string;
  subtitle?: string;
  alertDot?: boolean;
}

export const MOCK_KPI_DATA: KpiItem[] = [
  {
    label: '数据库总记录',
    value: '482,391',
    trend: '+2,847 today',
  },
  {
    label: '车站总数',
    value: '3,412',
    accentColor: 'green',
    subtitle: '坐标完成率 94.2%',
  },
  {
    label: '待处理告警',
    value: '3',
    accentColor: 'yellow',
    subtitle: '1 条需人工确认',
    alertDot: true,
  },
  {
    label: '今日 API 调用',
    value: '18,204',
    accentColor: 'purple',
    subtitle: '剩余: 81,796',
  },
];

export const MOCK_SPARKLINE_DATA = {
  values: [90, 72, 60, 45, 40, 22, 15],
  labels: ['03-24', '03-25', '03-26', '03-27', '03-28', '03-29', '今天'],
};

export const MOCK_API_QUOTA = {
  percentage: 75,
  used: 75_000,
  total: 100_000,
  label: '75%',
  sublabel: '75,000 / 100,000',
  resetDate: '04-01',
};
