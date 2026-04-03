import { Button } from '@vistaflow/ui';

interface HeaderProps {
  title: string;
  subtitle: string;
  onRefresh: () => void;
  timestamp: string;
}

export function Header({ title, subtitle, onRefresh, timestamp }: HeaderProps) {
  return (
    <header className="sticky top-0 z-30 bg-[#030303]/80 backdrop-blur-md border-b border-white/8 px-10 py-5 flex justify-between items-center">
      <div>
        <h1 className="font-serif text-2xl italic text-white">{title}</h1>
        <div className="text-xs text-muted mt-0.5">{subtitle}</div>
      </div>
      <div className="flex items-center gap-3">
        <Button variant="outline" onClick={onRefresh}>
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          刷新
        </Button>
        <div className="w-px h-5 bg-white/10" />
        <span className="text-xs text-muted">{timestamp}</span>
      </div>
    </header>
  );
}
