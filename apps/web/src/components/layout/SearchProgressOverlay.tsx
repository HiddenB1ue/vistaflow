import { useSearchProgressStore } from '@/stores/searchProgressStore';
import { useSearchStore } from '@/stores/searchStore';

function transferCountLabel(count: number): string {
  if (count === 0) return '直达方案';
  if (count === 1) return '一次换乘方案';
  if (count === 2) return '两次换乘方案';
  return `${count}次换乘方案`;
}

export function SearchProgressOverlay() {
  const { phase, plansReady, totalCandidates, errorMessage, currentTransferCount } =
    useSearchProgressStore();
  const params = useSearchStore((s) => s.params);

  if (phase === 'idle') {
    return null;
  }

  return (
    <div className="flex flex-col items-center gap-6 text-center">
      {/* Route info */}
      <div className="text-xs font-medium uppercase tracking-[0.25em] text-muted/60">
        {params.origin} → {params.destination}
        {params.date && <span className="ml-3">{params.date}</span>}
      </div>

      {/* Phase steps */}
      <div className="flex flex-col items-start gap-3 text-sm tracking-wider text-muted">
        {/* Plan steps */}
        {plansReady.map((plan) => (
          <div key={plan.transferCount} className="flex items-center gap-2">
            <span className="time-theme-text text-xs">✓</span>
            <span>
              {transferCountLabel(plan.transferCount)} — {plan.candidateCount} 条
            </span>
          </div>
        ))}

        {/* Currently planning */}
        {phase === 'planning' && currentTransferCount !== null && (
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 animate-pulse rounded-full time-theme-bg" />
            <span>正在搜索{transferCountLabel(currentTransferCount)}...</span>
          </div>
        )}

        {/* Candidates counted */}
        {totalCandidates !== null && (
          <div className="mt-1 text-xs text-muted/50">
            共 {totalCandidates} 条候选方案
          </div>
        )}

        {/* Building view */}
        {phase === 'building_view' && (
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 animate-pulse rounded-full time-theme-bg" />
            <span>正在整理结果...</span>
          </div>
        )}

        {/* Error */}
        {phase === 'error' && (
          <div className="flex flex-col items-center gap-4">
            <div className="text-sm text-red-400/80">
              {errorMessage ?? '搜索失败，请稍后重试'}
            </div>
            <button
              type="button"
              className="rounded-full border border-white/10 px-6 py-2.5 text-xs uppercase tracking-[0.2em] text-starlight transition-colors hover:bg-white/5"
              onClick={() => {
                window.location.href = '/';
              }}
            >
              返回搜索页
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
