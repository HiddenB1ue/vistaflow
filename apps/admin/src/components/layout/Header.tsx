
import { Button, PageHeader } from '@vistaflow/ui';
import { PAGE_LABELS } from '@/constants/labels';

interface HeaderProps {
  title: string;
  subtitle: string;
  onRefresh: () => void;
  timestamp: string;
  scrolled?: boolean;
}

export function Header({ title, subtitle, onRefresh, timestamp, scrolled = false }: HeaderProps) {
  return (
    <PageHeader
      sticky
      className={`admin-page-header${scrolled ? ' admin-page-header--scrolled' : ''}`}
      eyebrow={PAGE_LABELS.headerEyebrow}
      title={title}
      subtitle={subtitle}
      actions={(
        <>
          <Button variant="outline" onClick={onRefresh}>
            <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {PAGE_LABELS.refresh}
          </Button>
          <div className="h-5 w-px bg-white/10" />
          <span className="text-xs text-muted">{PAGE_LABELS.lastRefresh(timestamp)}</span>
        </>
      )}
    />
  );
}
