
import { useMemo, useState, type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { LOG_LABELS, TOAST_MESSAGES } from '@/constants/labels';
import { LogEntry } from '@/components/ui/LogEntry';
import { fetchLogs } from '@/services/logService';
import { useToastStore } from '@/stores/toastStore';
import {
  Button,
  ControlToolbar,
  ControlToolbarActions,
  ControlToolbarMain,
  CustomSelect,
  InputBox,
  PanelBody,
  PanelCard,
} from '@vistaflow/ui';

const severityOptions = [
  { value: 'all', label: LOG_LABELS.allSeverity },
  { value: 'INFO', label: 'INFO' },
  { value: 'WARN', label: 'WARN' },
  { value: 'ERROR', label: 'ERROR' },
  { value: 'SUCCESS', label: 'SUCCESS' },
  { value: 'SYSTEM', label: 'SYSTEM' },
];

function renderHighlightedMessage(message: string, terms?: string[]): ReactNode {
  if (!terms || terms.length === 0) return message;

  const parts: ReactNode[] = [];
  let remaining = message;
  let key = 0;

  while (remaining.length > 0) {
    let earliestIndex = -1;
    let earliestTerm = '';

    for (const term of terms) {
      const index = remaining.indexOf(term);
      if (index !== -1 && (earliestIndex === -1 || index < earliestIndex)) {
        earliestIndex = index;
        earliestTerm = term;
      }
    }

    if (earliestIndex === -1) {
      parts.push(remaining);
      break;
    }

    if (earliestIndex > 0) {
      parts.push(remaining.slice(0, earliestIndex));
    }

    parts.push(<span key={key += 1} className="text-[#4ADE80]">{earliestTerm}</span>);
    remaining = remaining.slice(earliestIndex + earliestTerm.length);
  }

  return <>{parts}</>;
}

export default function LogView() {
  const addToast = useToastStore((state) => state.addToast);
  const { data: logs = [] } = useQuery({
    queryKey: ['admin', 'logs'],
    queryFn: fetchLogs,
  });
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');

  const filteredLogs = useMemo(() => {
    const keyword = search.trim().toLowerCase();

    return logs.filter((log) => {
      const matchesKeyword = keyword.length === 0 || [log.timestamp, log.severity, log.message].some((field) => field.toLowerCase().includes(keyword));
      const matchesSeverity = severityFilter === 'all' || log.severity === severityFilter;
      return matchesKeyword && matchesSeverity;
    });
  }, [logs, search, severityFilter]);

  return (
    <div className="vf-page-stack">
      <ControlToolbar>
        <ControlToolbarMain>
          <InputBox placeholder={LOG_LABELS.searchPlaceholder} className="min-w-0 w-full" value={search} onChange={(event) => setSearch(event.target.value)} />
        </ControlToolbarMain>
        <ControlToolbarActions>
          <CustomSelect options={severityOptions} value={severityFilter} onChange={setSeverityFilter} className="w-full md:w-[180px]" />
          <Button variant="outline" size="sm" onClick={() => addToast(TOAST_MESSAGES.logsExported, 'success')}>
            {LOG_LABELS.exportLogs}
          </Button>
        </ControlToolbarActions>
      </ControlToolbar>

      <PanelCard>
        <PanelBody className="font-mono">
          {filteredLogs.map((log) => (
            <LogEntry key={log.id} timestamp={log.timestamp} severity={log.severity} message={renderHighlightedMessage(log.message, log.highlightedTerms)} />
          ))}
        </PanelBody>
      </PanelCard>
    </div>
  );
}
