
import { useEffect, useRef, useState, type RefObject } from 'react';
import { AuraBackground, ContentSection, DrawerBackdrop, NoiseTexture, type ComboboxInputRef } from '@vistaflow/ui';
import { Navbar } from '@/components/layout/Navbar';
import { FilterDrawer } from '@/components/overlays/FilterDrawer';
import { SEARCH_LABELS } from '@/constants/labels';
import { usePageTransition } from '@/hooks/usePageTransition';
import { useSearchReveal } from '@/hooks/useSearchReveal';
import { useTimeGreeting } from '@/hooks/useTimeGreeting';
import { useSearchStore } from '@/stores/searchStore';
import { useUiStore } from '@/stores/uiStore';
import type { SearchSuggestion } from '@/types/search';
import { GreetingHeader } from './GreetingHeader';
import { SearchHeroForm } from './SearchHeroForm';

export function SearchPage() {
  const { params, setOrigin, setDestination, setDate } = useSearchStore();
  const { greetingRef, headlineRef, formRef, btnRef } = useSearchReveal();
  const { navigateTo, revealPage } = usePageTransition();
  const greeting = useTimeGreeting();
  const {
    isSearchFilterOpen,
    searchFilterPrefs,
    setSearchFilterOpen,
    setSearchFilterPrefs,
  } = useUiStore();

  const originRef = useRef<ComboboxInputRef<SearchSuggestion>>(null);
  const destinationRef = useRef<ComboboxInputRef<SearchSuggestion>>(null);
  const dateInputRef = useRef<HTMLInputElement>(null);

  const [originError, setOriginError] = useState<string>('');
  const [destinationError, setDestinationError] = useState<string>('');

  useEffect(() => {
    revealPage();
  }, [revealPage]);

  const handleSearch = async () => {
    // Clear previous errors
    setOriginError('');
    setDestinationError('');

    // Validate inputs
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

    // Proceed to journey page
    navigateTo('/journey');
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden">
      <AuraBackground enableMouseTracking />
      <NoiseTexture />
      <DrawerBackdrop isActive={isSearchFilterOpen} onClick={() => setSearchFilterOpen(false)} />
      <Navbar onFilterOpen={() => setSearchFilterOpen(!isSearchFilterOpen)} />

      <FilterDrawer
        isOpen={isSearchFilterOpen}
        directOnly={searchFilterPrefs.directOnly}
        business={searchFilterPrefs.business}
        first={searchFilterPrefs.first}
        second={searchFilterPrefs.second}
        onDirectOnlyChange={(next) => setSearchFilterPrefs({ directOnly: next })}
        onBusinessChange={(next) => setSearchFilterPrefs({ business: next })}
        onFirstChange={(next) => setSearchFilterPrefs({ first: next })}
        onSecondChange={(next) => setSearchFilterPrefs({ second: next })}
        onClose={() => setSearchFilterOpen(false)}
      />

      <section
        id="hero-section"
        className="vf-page-gutter relative flex h-screen w-full flex-col items-center justify-center overflow-hidden"
      >
        <ContentSection spacing="hero" width="wide" className="text-center">
          <GreetingHeader greeting={greeting} greetingRef={greetingRef} headlineRef={headlineRef} />

          <SearchHeroForm
            origin={params.origin}
            destination={params.destination}
            date={params.date}
            formRef={formRef as RefObject<HTMLDivElement | null>}
            originRef={originRef}
            destinationRef={destinationRef}
            dateInputRef={dateInputRef}
            onOriginChange={setOrigin}
            onDestinationChange={setDestination}
            onDateChange={setDate}
            originError={originError}
            destinationError={destinationError}
          />

          <div className="mt-24 flex flex-col items-center gap-10">
            <button
              ref={btnRef as RefObject<HTMLButtonElement | null>}
              type="button"
              onClick={handleSearch}
              className="group relative cursor-pointer overflow-hidden rounded-full bg-starlight px-12 py-5 text-sm font-medium uppercase tracking-[0.2em] text-void transition-colors"
            >
              <span className="relative z-10 flex items-center gap-3">
                {SEARCH_LABELS.submitButton}
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </span>
              <div className="time-theme-bg absolute inset-0 translate-y-full transition-transform duration-500 group-hover:translate-y-0" />
            </button>
          </div>
        </ContentSection>
      </section>
    </div>
  );
}
