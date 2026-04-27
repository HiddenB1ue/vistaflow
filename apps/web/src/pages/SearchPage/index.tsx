import { useRef, useState, type RefObject } from 'react';
import {
  AuraBackground,
  ContentSection,
  DrawerBackdrop,
  NoiseTexture,
  type ComboboxInputRef,
} from '@vistaflow/ui';
import { Navbar } from '@/components/layout/Navbar';
import { SearchFilterDrawer } from '@/components/overlays/SearchFilterDrawer';
import { SEARCH_LABELS } from '@/constants/labels';
import { usePageTransition } from '@/hooks/usePageTransition';
import { useSearchReveal } from '@/hooks/useSearchReveal';
import { useTimeGreeting } from '@/hooks/useTimeGreeting';
import { createJourneySearchSession } from '@/services/routeService';
import { useRouteStore } from '@/stores/routeStore';
import { useSearchStore } from '@/stores/searchStore';
import { useUiStore } from '@/stores/uiStore';
import type { SearchSuggestion } from '@/types/search';
import { GreetingHeader } from './GreetingHeader';
import { SearchHeroForm } from './SearchHeroForm';

export function SearchPage() {
  const { params, setOrigin, setDestination, setDate, updateParams, setSearchId } =
    useSearchStore();
  const setViewResult = useRouteStore((state) => state.setViewResult);
  const setSortMode = useRouteStore((state) => state.setSortMode);
  const { greetingRef, headlineRef, formRef, btnRef } = useSearchReveal();
  const { navigateTo } = usePageTransition();
  const greeting = useTimeGreeting();
  const {
    isSearchFilterOpen,
    setSearchFilterOpen,
    resetJourneyFilterPrefs,
  } = useUiStore();

  const originRef = useRef<ComboboxInputRef<SearchSuggestion>>(null);
  const destinationRef = useRef<ComboboxInputRef<SearchSuggestion>>(null);
  const dateInputRef = useRef<HTMLInputElement>(null);

  const [originError, setOriginError] = useState<string>('');
  const [destinationError, setDestinationError] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSearch = async () => {
    setOriginError('');
    setDestinationError('');

    let hasError = false;

    if (!params.origin.trim()) {
      setOriginError('请输入出发地');
      hasError = true;
    }

    if (!params.destination.trim()) {
      setDestinationError('请输入目的地');
      hasError = true;
    }

    if (hasError) {
      return;
    }

    setIsSubmitting(true);
    try {
      const session = await createJourneySearchSession(params);
      resetJourneyFilterPrefs();
      setSearchId(session.searchId);
      setSortMode('duration');
      setViewResult(session.searchId, session.viewResult);
      navigateTo('/journey');
    } catch (error) {
      console.error('Failed to create journey search session:', error);
      setDestinationError('生成方案失败，请稍后重试');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden">
      <AuraBackground enableMouseTracking />
      <NoiseTexture />
      <DrawerBackdrop
        isActive={isSearchFilterOpen}
        onClick={() => setSearchFilterOpen(false)}
      />
      <Navbar onFilterOpen={() => setSearchFilterOpen(!isSearchFilterOpen)} />

      <SearchFilterDrawer
        isOpen={isSearchFilterOpen}
        params={params}
        onChange={updateParams}
        onClose={() => setSearchFilterOpen(false)}
      />

      <section
        id="hero-section"
        className="vf-page-gutter relative flex h-screen w-full flex-col items-center justify-center overflow-hidden"
      >
        <ContentSection spacing="hero" width="wide" className="text-center">
          <GreetingHeader
            greeting={greeting}
            greetingRef={greetingRef}
            headlineRef={headlineRef}
          />

          <SearchHeroForm
            origin={params.origin}
            destination={params.destination}
            date={params.date}
            formRef={formRef as RefObject<HTMLDivElement | null>}
            originRef={originRef as RefObject<ComboboxInputRef<SearchSuggestion>>}
            destinationRef={destinationRef as RefObject<ComboboxInputRef<SearchSuggestion>>}
            dateInputRef={dateInputRef as RefObject<HTMLInputElement>}
            onOriginChange={setOrigin}
            onDestinationChange={setDestination}
            onDateChange={setDate}
            originError={originError}
            destinationError={destinationError}
          />

          <div className="mt-6 text-sm tracking-[0.14em] text-muted">
            当前搜索规则：最多换乘 {params.transferCount} 次，最短换乘{' '}
            {params.minTransferMinutes} 分钟
          </div>

          <div className="mt-24 flex flex-col items-center gap-10">
            <button
              ref={btnRef as RefObject<HTMLButtonElement | null>}
              type="button"
              onClick={handleSearch}
              disabled={isSubmitting}
              className={`group relative overflow-hidden rounded-full bg-starlight px-12 py-5 text-sm font-medium uppercase tracking-[0.2em] text-void transition-colors ${
                isSubmitting ? 'cursor-default' : 'cursor-pointer'
              }`}
            >
              <span className="relative z-10 flex items-center">
                {isSubmitting ? '生成中...' : SEARCH_LABELS.submitButton}
              </span>
              <div
                className={`time-theme-bg absolute inset-0 transition-transform duration-500 ${
                  isSubmitting ? 'translate-y-0' : 'translate-y-full group-hover:translate-y-0'
                }`}
              />
            </button>
          </div>
        </ContentSection>
      </section>
    </div>
  );
}
