import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ContentSection } from '@vistaflow/ui';
import { fetchActiveTasks, fetchApiQuota, fetchKpiStats, fetchSparklineData, fetchSystemAlerts } from '@/services/overviewService';
import { useToastStore } from '@/stores/toastStore';
import { OverviewInsightsSection, OverviewKpiGrid, OverviewTrendSection } from './overviewSections';

export default function OverviewView() {
  const [range, setRange] = useState<'7d' | '30d'>('7d');
  const addToast = useToastStore((state) => state.addToast);
  
  const { data: sparklineData, isLoading: sparklineLoading, error: sparklineError } = useQuery({
    queryKey: ['admin', 'overview', 'sparkline', range],
    queryFn: () => fetchSparklineData(range === '7d' ? 7 : 30),
  });
  
  const { data: apiQuota, isLoading: quotaLoading, error: quotaError } = useQuery({
    queryKey: ['admin', 'overview', 'quota'],
    queryFn: fetchApiQuota,
  });
  
  const { data: kpiStats, isLoading: kpiLoading, error: kpiError } = useQuery({
    queryKey: ['admin', 'overview', 'kpi'],
    queryFn: fetchKpiStats,
  });
  
  const { data: activeTasks, isLoading: tasksLoading, error: tasksError } = useQuery({
    queryKey: ['admin', 'overview', 'tasks'],
    queryFn: fetchActiveTasks,
  });
  
  const { data: systemAlerts, isLoading: alertsLoading, error: alertsError } = useQuery({
    queryKey: ['admin', 'overview', 'alerts'],
    queryFn: fetchSystemAlerts,
  });

  // Show error toasts
  useEffect(() => {
    if (sparklineError) addToast('加载趋势数据失败', 'error');
  }, [sparklineError, addToast]);

  useEffect(() => {
    if (quotaError) addToast('加载配额数据失败', 'error');
  }, [quotaError, addToast]);

  useEffect(() => {
    if (kpiError) addToast('加载KPI数据失败', 'error');
  }, [kpiError, addToast]);

  useEffect(() => {
    if (tasksError) addToast('加载任务数据失败', 'error');
  }, [tasksError, addToast]);

  useEffect(() => {
    if (alertsError) addToast('加载告警数据失败', 'error');
  }, [alertsError, addToast]);

  return (
    <div className="vf-page-stack">
      <ContentSection spacing="dense">
        <OverviewKpiGrid kpiStats={kpiStats} isLoading={kpiLoading} />
      </ContentSection>

      <ContentSection spacing="dense">
        <OverviewTrendSection
          range={range}
          onRangeChange={setRange}
          sparklineData={sparklineData}
          apiQuota={apiQuota}
          isLoading={sparklineLoading || quotaLoading}
        />
      </ContentSection>

      <ContentSection spacing="dense">
        <OverviewInsightsSection
          activeTasks={activeTasks}
          systemAlerts={systemAlerts}
          isLoading={tasksLoading || alertsLoading}
        />
      </ContentSection>
    </div>
  );
}
