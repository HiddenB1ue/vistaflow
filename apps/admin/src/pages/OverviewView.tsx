import { usePanelReveal } from '@/hooks/usePanelReveal';
import { KpiCard } from '@/components/ui/KpiCard';
import { SparklineChart } from '@/components/ui/SparklineChart';
import { DonutChart } from '@/components/ui/DonutChart';
import { StatusDot } from '@/components/ui/StatusDot';
import { Badge } from '@/components/ui/Badge';
import { MOCK_SPARKLINE_DATA, MOCK_API_QUOTA } from '@/services/mock/overview.mock';

interface OverviewViewProps {
  onNavigateToTasks: () => void;
  onNavigateToLog: () => void;
}

export function OverviewView({ onNavigateToTasks, onNavigateToLog }: OverviewViewProps) {
  const { containerRef } = usePanelReveal();

  return (
    <div ref={containerRef}>
      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        <KpiCard
          label="数据库总记录"
          value="482,391"
          trend={
            <>
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
              今日 +2,847
            </>
          }
        />
        <KpiCard label="覆盖车站数" value="3,412" accentColor="#4ADE80" valueClassName="text-[#4ADE80]"
          subtitle={<>坐标补全率 <span className="text-[#4ADE80]">94.2%</span></>}
        />
        <KpiCard label="待处理告警" value="3" accentColor="#FACC15" alertDot valueClassName="text-[#FACC15]"
          subtitle="1 需人工确认"
        />
        <KpiCard label="今日 API 调用" value="18,204" accentColor="#8B5CF6" valueClassName="text-[#C4B5FD]"
          subtitle={<>余量 <span className="text-[#C4B5FD]">81,796</span></>}
        />
      </div>

      {/* Middle: Sparkline + Donut */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-8">
        <div className="glass-panel p-6 lg:col-span-2">
          <div className="flex justify-between items-center mb-6">
            <div>
              <div className="text-[10px] text-muted tracking-widest uppercase mb-1">数据录入趋势</div>
              <div className="font-display text-lg">近 7 天</div>
            </div>
            <div className="flex gap-2">
              <button className="tab-btn active text-xs">7天</button>
              <button className="tab-btn text-xs">30天</button>
            </div>
          </div>
          <SparklineChart data={MOCK_SPARKLINE_DATA.values} labels={MOCK_SPARKLINE_DATA.labels} />
        </div>

        <div className="glass-panel p-6 flex flex-col">
          <div className="text-[10px] text-muted tracking-widest uppercase mb-1">API 配额使用率</div>
          <div className="font-display text-lg mb-6">高德地图</div>
          <div className="flex-1 flex flex-col items-center justify-center">
            <DonutChart percentage={MOCK_API_QUOTA.percentage} label={MOCK_API_QUOTA.label} sublabel="已使用" />
            <div className="text-xs text-muted mt-4 text-center">
              已用 {MOCK_API_QUOTA.used.toLocaleString()} / {MOCK_API_QUOTA.total.toLocaleString()} 次<br />
              重置于 {MOCK_API_QUOTA.resetDate}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom: Active tasks + Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="glass-panel p-6">
          <div className="flex justify-between items-center mb-5">
            <div className="text-sm font-display tracking-wide">活跃任务</div>
            <button className="text-xs text-muted hover:text-white transition-colors cursor-pointer" onClick={onNavigateToTasks}>查看全部 →</button>
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-3 py-2 border-b border-white/4">
              <StatusDot variant="running" />
              <span className="text-sm flex-1">车次状态同步 T+15</span>
              <span className="font-mono text-xs text-[#4ADE80]">00:15:22</span>
            </div>
            <div className="flex items-center gap-3 py-2 border-b border-white/4">
              <StatusDot variant="pending" />
              <span className="text-sm flex-1">站点经纬度补全</span>
              <Badge variant="yellow">待确认</Badge>
            </div>
            <div className="flex items-center gap-3 py-2">
              <StatusDot variant="idle" />
              <span className="text-sm flex-1 text-muted">基础车站全量抓取</span>
              <Badge variant="blue">Completed</Badge>
            </div>
          </div>
        </div>

        <div className="glass-panel p-6">
          <div className="flex justify-between items-center mb-5">
            <div className="text-sm font-display tracking-wide">系统告警</div>
            <button className="text-xs text-muted hover:text-white transition-colors cursor-pointer" onClick={onNavigateToLog}>查看日志 →</button>
          </div>
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-[#FACC15]/5 border border-[#FACC15]/15">
              <svg className="w-4 h-4 text-[#FACC15] shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div>
                <div className="text-xs font-display text-[#FACC15]">代理凭证已过期</div>
                <div className="text-xs text-muted mt-0.5">票务查询代理 Token 失效，影响实时票价查询</div>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 rounded-lg bg-[#8B5CF6]/5 border border-[#8B5CF6]/15">
              <svg className="w-4 h-4 text-[#C4B5FD] shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <div className="text-xs font-display text-[#C4B5FD]">API 配额预警</div>
                <div className="text-xs text-muted mt-0.5">高德地图 API 已用 75%，预计 2 天后耗尽</div>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 rounded-lg bg-[#4ADE80]/5 border border-[#4ADE80]/15">
              <svg className="w-4 h-4 text-[#4ADE80] shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <div>
                <div className="text-xs font-display text-[#4ADE80]">全量抓取完成</div>
                <div className="text-xs text-muted mt-0.5">共入库 3,412 条车站记录，耗时 2m 14s</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
