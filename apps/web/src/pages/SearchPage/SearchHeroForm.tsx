
import type { RefObject } from 'react';
import type { SearchSuggestion } from '@/types/search';
import { fetchStationSuggestions } from '@/services/stationService';
import { ComboboxInput, DatePicker } from '@vistaflow/ui';
import { DATE_PICKER_LABELS, SEARCH_LABELS } from '@/constants/labels';

interface SearchHeroFormProps {
  origin: string;
  destination: string;
  date: string;
  formRef: RefObject<HTMLDivElement | null>;
  onOriginChange: (value: string) => void;
  onDestinationChange: (value: string) => void;
  onDateChange: (value: string) => void;
}

export function SearchHeroForm({
  origin,
  destination,
  date,
  formRef,
  onOriginChange,
  onDestinationChange,
  onDateChange,
}: SearchHeroFormProps) {
  return (
    <div
      ref={formRef}
      className="flex flex-wrap items-center justify-center gap-y-8 text-2xl font-light leading-relaxed tracking-wide md:text-3xl"
    >
      <span className="text-muted">{SEARCH_LABELS.fromPrefix}</span>
      <ComboboxInput<SearchSuggestion>
        appearance="hero"
        value={origin}
        onValueChange={onOriginChange}
        loadOptions={fetchStationSuggestions}
        getOptionId={(item) => item.id}
        getOptionLabel={(item) => item.name}
        getOptionDescription={(item) => item.code}
        placeholder={SEARCH_LABELS.originPlaceholder}
        aria-label={SEARCH_LABELS.originPlaceholder}
        className="mx-4"
      />
      <span className="text-muted">{SEARCH_LABELS.fromSuffix}</span>
      <ComboboxInput<SearchSuggestion>
        appearance="hero"
        value={destination}
        onValueChange={onDestinationChange}
        loadOptions={fetchStationSuggestions}
        getOptionId={(item) => item.id}
        getOptionLabel={(item) => item.name}
        getOptionDescription={(item) => item.code}
        placeholder={SEARCH_LABELS.destinationPlaceholder}
        aria-label={SEARCH_LABELS.destinationPlaceholder}
        className="mx-4"
      />
      <span className="text-muted">{SEARCH_LABELS.datePrefix}</span>
      <DatePicker
        appearance="hero"
        value={date}
        onChange={onDateChange}
        className="mx-4"
        labels={DATE_PICKER_LABELS}
        presets={DATE_PICKER_LABELS.presets.map((preset) => ({ ...preset }))}
      />
      <span className="text-muted">{SEARCH_LABELS.dateSuffix}</span>
    </div>
  );
}
