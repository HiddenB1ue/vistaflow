import { useNavigate } from 'react-router-dom';
import {
  Badge,
  Button,
  DonutChart,
  KpiCard,
  PanelBody,
  PanelCard,
  SectionHeader,
  SegmentedControl,
  SparklineChart,
  StatusDot,
} from '@vistaflow/ui';
import { OVERVIEW_LABELS } from '@/constants/labels';
import type { ActiveTask, ApiQuota, KpiStats, SparklineData, SystemAlert } from '@/types/overview';

interface OverviewKpiGridProps {
  kpiStats?: KpiStats;
  isLoading?: boolean;
}

interface OverviewTrendSectionProps {
  range: '7d' | '30d';
  onRangeChange: (value: '7d' | '30d') => void;
  sparklineData?: SparklineData;
  apiQuota?: ApiQuota;
  isLoading?: boolean;
}

interface OverviewInsightsSectionProps {
  activeTasks?: ActiveTask[];
  systemAlerts?: SystemAlert[];
  isLoading?: boolean;
}

export function OverviewKpiGrid({ kpiStats, isLoading }: OverviewKpiGridProps) {
  if (isLoading || !kpiStats) {
    return (
      <div className="grid grid-cols-2 gap-5 lg:grid-cols-4">
        <KpiCard label={OVERVIEW_LABELS.totalRecords} value="--" />
        <KpiCard label={OVERVIEW_LABELS.stationCoverage} value="--" />
        <KpiCard label={OVERVIEW_LABELS.pendingAlerts} value="--" />
        <KpiCard label={OVERVIEW_LABELS.todayApiCalls} value="--" />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-5 lg:grid-cols-4">
      <KpiCard
        label={OVERVIEW_LABELS.totalRecords}
        value={kpiStats.totalRecords.toLocaleString('zh-CN')}
        trend={(
          <>
            <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
            </svg>
            {OVERVIEW_LABELS.totalRecordsTrend}
          </>
        )}
      />
      <KpiCard
        label={OVERVIEW_LABELS.stationCoverage}
        value={kpiStats.stationCoverage.toLocaleString('zh-CN')}
        accentColor="#4ADE80"
        valueClassName="text-[#4ADE80]"
        subtitle={<>{OVERVIEW_LABELS.coordCompletion} <span className="text-[#4ADE80]">{kpiStats.coordCompletionRate}%</span></>}
      />
      <KpiCard
        label={OVERVIEW_LABELS.pendingAlerts}
        value={kpiStats.pendingAlerts.toString()}
        accentColor="#FACC15"
        alertDot={kpiStats.pendingAlerts > 0}
        valueClassName="text-[#FACC15]"
        subtitle={OVERVIEW_LABELS.pendingAlertsSubtitle}
      />
      <KpiCard
        label={OVERVIEW_LABELS.todayApiCalls}
        value={kpiStats.todayApiCalls.toLocaleString('zh-CN')}
        accentColor="#8B5CF6"
        valueClassName="text-[#C4B5FD]"
        subtitle={<>{OVERVIEW_LABELS.remainingQuota} <span className="text-[#C4B5FD]">{kpiStats.remainingQuota.toLocaleString('zh-CN')}</span></>}
      />
    </div>
  );
}

export function OverviewTrendSection({ range, onRangeChange, sparklineData, apiQuota, isLoading }: OverviewTrendSectionProps) {
  const resolvedSparklineData = sparklineData ?? { values: [], labels: [] };
  const resolvedApiQuota = apiQuota ?? {
    percentage: 0,
    used: 0,
    total: 0,
  };

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
      <PanelCard className="lg:col-span-2">
        <SectionHeader
          eyebrow={OVERVIEW_LABELS.dataPulse}
          title={OVERVIEW_LABELS.dataIngestionTrend}
          subtitle={OVERVIEW_LABELS.trendSubtitle}
          actions={(
            <SegmentedControl
              size="sm"
              value={range}
              onChange={onRangeChange}
              options={[
                { value: '7d', label: OVERVIEW_LABELS.range7d },
                { value: '30d', label: OVERVIEW_LABELS.range30d },
              ]}
            />
          )}
        />
        <PanelBody>
          {isLoading ? (
            <div className="flex h-48 items-center justify-center text-muted">加载中...</div>
          ) : (
            <SparklineChart data={resolvedSparklineData.values} labels={resolvedSparklineData.labels} />
          )}
        </PanelBody>
      </PanelCard>

      <PanelCard>
        <SectionHeader eyebrow="配额" title={OVERVIEW_LABELS.apiUsage} subtitle={OVERVIEW_LABELS.amapService} />
        <PanelBody className="flex-1 items-center justify-center text-center">
          {isLoading ? (
            <div className="flex h-48 items-center justify-center text-muted">加载中...</div>
          ) : (
            <>
              <DonutChart percentage={resolvedApiQuota.percentage} label={`${resolvedApiQuota.percentage}%`} sublabel={OVERVIEW_LABELS.quotaUsed} />
              <div className="text-xs text-muted">
                {OVERVIEW_LABELS.quotaUsed} {resolvedApiQuota.used.toLocaleString('zh-CN')} / {resolvedApiQuota.total.toLocaleString('zh-CN')} 次
              </div>
            </>
          )}
        </PanelBody>
      </PanelCard>
    </div>
  );
}

export function OverviewInsightsSection({ activeTasks, systemAlerts, isLoading }: OverviewInsightsSectionProps) {
  const navigate = useNavigate();

  const statusVariantMap: Record<string, 'running' | 'pending' | 'idle'> = {
    running: 'running',
    pending: 'pending',
    completed: 'idle',
  };

  const severityColorMap: Record<string, string> = {
    warning: '#FACC15',
    info: '#8B5CF6',
    success: '#4ADE80',
  };

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
      <PanelCard>
        <SectionHeader
          eyebrow={OVERVIEW_LABELS.operationsEyebrow}
          title={OVERVIEW_LABELS.activeTasks}
          actions={<Button variant="outline" size="sm" onClick={() => navigate('/tasks')}>{OVERVIEW_LABELS.viewAll}</Button>}
        />
        <PanelBody className="space-y-3">
          {isLoading ? (
            <div className="py-4 text-center text-sm text-muted">加载中...</div>
          ) : activeTasks && activeTasks.length > 0 ? (
            activeTasks.map((task, index) => (
              <div key={task.id} className={`flex items-center gap-3 ${index < activeTasks.length - 1 ? 'border-b border-white/4' : ''} py-2`}>
                <StatusDot variant={statusVariantMap[task.status] || 'idle'} />
                <span className="flex-1 text-sm">{task.name}</span>
                {task.elapsedTime ? (
                  <span className="font-mono text-xs text-[#4ADE80]">{task.elapsedTime}</span>
                ) : (
                  <Badge variant={task.status === 'pending' ? 'yellow' : 'blue'}>
                    {task.status === 'pending' ? OVERVIEW_LABELS.pendingBadge : OVERVIEW_LABELS.completedBadge}
                  </Badge>
                )}
              </div>
            ))
          ) : (
            <div className="py-4 text-center text-sm text-muted">暂无活跃任务</div>
          )}
        </PanelBody>
      </PanelCard>

      <PanelCard>
        <SectionHeader
          eyebrow={OVERVIEW_LABELS.signalEyebrow}
          title={OVERVIEW_LABELS.systemAlerts}
          actions={<Button variant="outline" size="sm" onClick={() => navigate('/log')}>{OVERVIEW_LABELS.viewLogs}</Button>}
        />
        <PanelBody className="space-y-3">
          {isLoading ? (
            <div className="py-4 text-center text-sm text-muted">加载中...</div>
          ) : systemAlerts && systemAlerts.length > 0 ? (
            systemAlerts.map((alert) => {
              const color = severityColorMap[alert.severity] || '#8B5CF6';
              const iconPath = alert.severity === 'warning'
                ? 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
                : alert.severity === 'success'
                ? 'M5 13l4 4L19 7'
                : 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z';

              return (
                <div 
                  key={alert.id} 
                  className="flex items-start gap-3 rounded-lg p-3"
                  style={{ 
                    border: `1px solid ${color}15`,
                    backgroundColor: `${color}0D`,
                    outline: 'none'
                  }}
                  tabIndex={-1}
                  onFocus={(e) => e.currentTarget.blur()}
                >
                  <svg className="mt-0.5 h-4 w-4 shrink-0" style={{ color }} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={iconPath} />
                  </svg>
                  <div className="pointer-events-none">
                    <div className="text-xs font-display" style={{ color }}>{alert.title}</div>
                    <div className="mt-0.5 text-xs text-muted">{alert.message}</div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="py-4 text-center text-sm text-muted">暂无系统告警</div>
          )}
        </PanelBody>
      </PanelCard>
    </div>
  );
}
