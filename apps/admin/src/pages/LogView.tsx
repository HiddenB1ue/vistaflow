import { useState } from 'react';
import type { ToastType } from '@/stores/uiStore';
import { MOCK_LOGS } from '@/services/mock/logs.mock';
import { InputBox } from '@/components/ui/InputBox';
import { CustomSelect } from '@/components/ui/CustomSelect';
import { Button } from '@/components/ui/Button';
import { LogEntry } from '@/components/ui/LogEntry';

interface LogViewProps {
  addToast: (message: string, type: ToastType) => void;
}

const severityOptions = [
  { value: 'all', label: '所有级别' },
  { value: 'info', label: 'INFO' },
  { value: 'warn', label: 'WARN' },
  { value: 'error', label: 'ERROR' },
  { value: 'success', label: 'SUCCESS' },
];

function renderHighlightedMessage(message: string, terms?: string[]): React.ReactNode {
  if (!terms || terms.length === 0) return message;

  const parts: React.ReactNode[] = [];
  let remaining = message;
  let keyIdx = 0;

  while (remaining.length > 0) {
    let earliestIdx = -1;
    let earliestTerm = '';

    for (const term of terms) {
      const idx = remaining.indexOf(term);
      if (idx !== -1 && (earliestIdx === -1 || idx < earliestIdx)) {
        earliestIdx = idx;
        earliestTerm = term;
      }
    }

    if (earliestIdx === -1) {
      parts.push(remaining);
      break;
    }

    if (earliestIdx > 0) {
      parts.push(remaining.slice(0, earliestIdx));
    }
    parts.push(
      <span key={keyIdx++} className="text-[#4ADE80]">{earliestTerm}</span>,
    );
    remaining = remaining.slice(earliestIdx + earliestTerm.length);
  }

  return <>{parts}</>;
}

export function LogView({ addToast }: LogViewProps) {
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');

  return (
    <div>
      <div className="flex flex-wrap gap-3 mb-6">
        <InputBox placeholder="搜索关键词…" className="flex-1 min-w-48" value={search} onChange={(e) => setSearch(e.target.value)} />
        <CustomSelect options={severityOptions} value={severityFilter} onChange={setSeverityFilter} className="w-[155px]" />
        <Button variant="outline" size="sm" onClick={() => addToast('日志已导出', 'success')}>导出日志</Button>
      </div>

      <div className="glass-panel p-5 font-mono">
        {MOCK_LOGS.map((log) => (
          <LogEntry
            key={log.id}
            timestamp={log.timestamp}
            severity={log.severity}
            message={renderHighlightedMessage(log.message, log.highlightedTerms)}
          />
        ))}
      </div>
    </div>
  );
}
