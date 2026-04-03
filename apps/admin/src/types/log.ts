export type LogSeverity = 'SUCCESS' | 'INFO' | 'WARN' | 'ERROR' | 'SYSTEM';

export interface LogRecord {
  id: string;
  timestamp: string;
  severity: LogSeverity;
  message: string;
  highlightedTerms?: string[];
}
