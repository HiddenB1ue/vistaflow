interface SearchFormProps {
  origin: string;
  destination: string;
  date: string;
  onOriginChange: (v: string) => void;
  onDestinationChange: (v: string) => void;
  onDateChange: (v: string) => void;
  onSubmit: () => void;
}

export function SearchForm({
  origin,
  destination,
  date,
  onOriginChange,
  onDestinationChange,
  onDateChange,
  onSubmit,
}: SearchFormProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!origin.trim() || !destination.trim() || !date.trim()) return;
    onSubmit();
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div
        className="text-2xl md:text-3xl font-light tracking-wide flex flex-wrap justify-center items-center gap-y-8 leading-relaxed"
        style={{ fontFamily: 'Inter, sans-serif' }}
      >
        <span style={{ color: 'var(--color-text-secondary)' }}>我想从</span>
        <input
          type="text"
          value={origin}
          onChange={(e) => onOriginChange(e.target.value)}
          placeholder="出发地"
          aria-label="出发地"
          className="mx-4 bg-transparent border-b outline-none text-center transition-all duration-300"
          style={{
            borderBottomColor: 'rgba(255,255,255,0.2)',
            color: 'var(--color-pulse)',
            fontFamily: '"Space Grotesk", sans-serif',
            fontSize: '1.5rem',
            width: '140px',
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderBottomColor = 'var(--color-pulse)';
            e.currentTarget.style.width = '180px';
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderBottomColor = 'rgba(255,255,255,0.2)';
            e.currentTarget.style.width = '140px';
          }}
        />
        <span style={{ color: 'var(--color-text-secondary)' }}>出发，前往</span>
        <input
          type="text"
          value={destination}
          onChange={(e) => onDestinationChange(e.target.value)}
          placeholder="目的地"
          aria-label="目的地"
          className="mx-4 bg-transparent border-b outline-none text-center transition-all duration-300"
          style={{
            borderBottomColor: 'rgba(255,255,255,0.2)',
            color: 'var(--color-pulse)',
            fontFamily: '"Space Grotesk", sans-serif',
            fontSize: '1.5rem',
            width: '140px',
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderBottomColor = 'var(--color-pulse)';
            e.currentTarget.style.width = '180px';
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderBottomColor = 'rgba(255,255,255,0.2)';
            e.currentTarget.style.width = '140px';
          }}
        />
        <span style={{ color: 'var(--color-text-secondary)' }}>，</span>
        <span
          className="w-full md:w-auto mt-4 md:mt-0"
          style={{ color: 'var(--color-text-secondary)' }}
        >
          日期是
        </span>
        <input
          type="text"
          value={date}
          onChange={(e) => onDateChange(e.target.value)}
          placeholder="出行日期"
          aria-label="出行日期"
          className="mx-4 bg-transparent border-b outline-none text-center transition-all duration-300"
          style={{
            borderBottomColor: 'rgba(255,255,255,0.2)',
            color: 'var(--color-pulse)',
            fontFamily: '"Space Grotesk", sans-serif',
            fontSize: '1.5rem',
            width: '160px',
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderBottomColor = 'var(--color-pulse)';
            e.currentTarget.style.width = '200px';
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderBottomColor = 'rgba(255,255,255,0.2)';
            e.currentTarget.style.width = '160px';
          }}
        />
        <span style={{ color: 'var(--color-text-secondary)' }}>。</span>
      </div>
    </form>
  );
}
