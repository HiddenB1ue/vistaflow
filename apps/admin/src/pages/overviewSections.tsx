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
import type { ApiQuota, SparklineData } from '@/services/overviewService';

interface OverviewTrendSectionProps {
  range: '7d' | '30d';
  onRangeChange: (value: '7d' | '30d') => void;
  sparklineData?: SparklineData;
  apiQuota?: ApiQuota;
}

export function OverviewKpiGrid() {
  return (
    <div className="grid grid-cols-2 gap-5 lg:grid-cols-4">
      <KpiCard
        label={OVERVIEW_LABELS.totalRecords}
        value="482,391"
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
        value="3,412"
        accentColor="#4ADE80"
        valueClassName="text-[#4ADE80]"
        subtitle={<>{OVERVIEW_LABELS.coordCompletion} <span className="text-[#4ADE80]">94.2%</span></>}
      />
      <KpiCard
        label={OVERVIEW_LABELS.pendingAlerts}
        value="3"
        accentColor="#FACC15"
        alertDot
        valueClassName="text-[#FACC15]"
        subtitle={OVERVIEW_LABELS.pendingAlertsSubtitle}
      />
      <KpiCard
        label={OVERVIEW_LABELS.todayApiCalls}
        value="18,204"
        accentColor="#8B5CF6"
        valueClassName="text-[#C4B5FD]"
        subtitle={<>{OVERVIEW_LABELS.remainingQuota} <span className="text-[#C4B5FD]">81,796</span></>}
      />
    </div>
  );
}

export function OverviewTrendSection({ range, onRangeChange, sparklineData, apiQuota }: OverviewTrendSectionProps) {
  const resolvedSparklineData = sparklineData ?? { values: [], labels: [] };
  const resolvedApiQuota = apiQuota ?? {
    percentage: 0,
    used: 0,
    total: 0,
    label: '0%',
    sublabel: '0 / 0',
    resetDate: '--',
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
          <SparklineChart data={resolvedSparklineData.values} labels={resolvedSparklineData.labels} />
        </PanelBody>
      </PanelCard>

      <PanelCard>
        <SectionHeader eyebrow="配额" title={OVERVIEW_LABELS.apiUsage} subtitle={OVERVIEW_LABELS.amapService} />
        <PanelBody className="flex-1 items-center justify-center text-center">
          <DonutChart percentage={resolvedApiQuota.percentage} label={resolvedApiQuota.label} sublabel={OVERVIEW_LABELS.quotaUsed} />
          <div className="text-xs text-muted">
            {OVERVIEW_LABELS.quotaUsed} {resolvedApiQuota.used.toLocaleString('zh-CN')} / {resolvedApiQuota.total.toLocaleString('zh-CN')} 次
            <br />
            {OVERVIEW_LABELS.quotaReset}{resolvedApiQuota.resetDate}
          </div>
        </PanelBody>
      </PanelCard>
    </div>
  );
}

export function OverviewInsightsSection() {
  const navigate = useNavigate();

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
      <PanelCard>
        <SectionHeader
          eyebrow={OVERVIEW_LABELS.operationsEyebrow}
          title={OVERVIEW_LABELS.activeTasks}
          actions={<Button variant="outline" size="sm" onClick={() => navigate('/tasks')}>{OVERVIEW_LABELS.viewAll}</Button>}
        />
        <PanelBody className="space-y-3">
          <div className="flex items-center gap-3 border-b border-white/4 py-2">
            <StatusDot variant="running" />
            <span className="flex-1 text-sm">{OVERVIEW_LABELS.taskSyncName}</span>
            <span className="font-mono text-xs text-[#4ADE80]">00:15:22</span>
          </div>
          <div className="flex items-center gap-3 border-b border-white/4 py-2">
            <StatusDot variant="pending" />
            <span className="flex-1 text-sm">{OVERVIEW_LABELS.taskReviewName}</span>
            <Badge variant="yellow">{OVERVIEW_LABELS.pendingBadge}</Badge>
          </div>
          <div className="flex items-center gap-3 py-2">
            <StatusDot variant="idle" />
            <span className="flex-1 text-sm text-muted">{OVERVIEW_LABELS.taskFullFetchName}</span>
            <Badge variant="blue">{OVERVIEW_LABELS.completedBadge}</Badge>
          </div>
        </PanelBody>
      </PanelCard>

      <PanelCard>
        <SectionHeader
          eyebrow={OVERVIEW_LABELS.signalEyebrow}
          title={OVERVIEW_LABELS.systemAlerts}
          actions={<Button variant="outline" size="sm" onClick={() => navigate('/log')}>{OVERVIEW_LABELS.viewLogs}</Button>}
        />
        <PanelBody className="space-y-3">
          <div className="flex items-start gap-3 rounded-lg border border-[#FACC15]/15 bg-[#FACC15]/5 p-3">
            <svg className="mt-0.5 h-4 w-4 shrink-0 text-[#FACC15]" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <div className="text-xs font-display text-[#FACC15]">{OVERVIEW_LABELS.credentialExpired}</div>
              <div className="mt-0.5 text-xs text-muted">{OVERVIEW_LABELS.credentialExpiredDesc}</div>
            </div>
          </div>
          <div className="flex items-start gap-3 rounded-lg border border-[#8B5CF6]/15 bg-[#8B5CF6]/5 p-3">
            <svg className="mt-0.5 h-4 w-4 shrink-0 text-[#C4B5FD]" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <div className="text-xs font-display text-[#C4B5FD]">{OVERVIEW_LABELS.apiQuotaWarning}</div>
              <div className="mt-0.5 text-xs text-muted">{OVERVIEW_LABELS.apiQuotaWarningDesc}</div>
            </div>
          </div>
          <div className="flex items-start gap-3 rounded-lg border border-[#4ADE80]/15 bg-[#4ADE80]/5 p-3">
            <svg className="mt-0.5 h-4 w-4 shrink-0 text-[#4ADE80]" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <div>
              <div className="text-xs font-display text-[#4ADE80]">{OVERVIEW_LABELS.fullSyncDone}</div>
              <div className="mt-0.5 text-xs text-muted">{OVERVIEW_LABELS.fullSyncDoneDesc}</div>
            </div>
          </div>
        </PanelBody>
      </PanelCard>
    </div>
  );
}
