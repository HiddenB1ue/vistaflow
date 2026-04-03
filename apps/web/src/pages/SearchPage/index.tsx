import { useEffect } from 'react';
import { DatePicker } from '@/components/ui/DatePicker';
import { StationInput } from '@/components/ui/StationInput';
import { AuraBackground, NoiseTexture } from '@vistaflow/ui';
import { Navbar } from '@/components/layout/Navbar';
import { FilterDrawer } from '@/components/overlays/FilterDrawer';
import { useSearchStore } from '@/stores/searchStore';
import { useUiStore } from '@/stores/uiStore';
import { useSearchReveal } from '@/hooks/useSearchReveal';
import { usePageTransition } from '@/hooks/usePageTransition';
import { useTimeGreeting } from '@/hooks/useTimeGreeting';

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

  useEffect(() => {
    revealPage();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSearch = () => {
    navigateTo('/journey');
  };

  return (
    <div className="relative min-h-screen overflow-hidden flex items-center justify-center">
      <AuraBackground enableMouseTracking={true} />
      <NoiseTexture />
      <Navbar onFilterOpen={() => setSearchFilterOpen(!isSearchFilterOpen)} />

      <FilterDrawer
        isOpen={isSearchFilterOpen}
        directOnly={searchFilterPrefs.directOnly}
        business={searchFilterPrefs.business}
        first={searchFilterPrefs.first}
        second={searchFilterPrefs.second}
        onDirectOnlyChange={(v) => setSearchFilterPrefs({ directOnly: v })}
        onBusinessChange={(v) => setSearchFilterPrefs({ business: v })}
        onFirstChange={(v) => setSearchFilterPrefs({ first: v })}
        onSecondChange={(v) => setSearchFilterPrefs({ second: v })}
        onClose={() => setSearchFilterOpen(false)}
      />

      {/* Hero 内容区 */}
      <section
        id="hero-section"
        className="relative h-screen flex flex-col items-center justify-center w-full px-6 overflow-hidden"
        style={{ zIndex: 10 }}
      >
        <div className="text-center w-full max-w-6xl">
          {/* 标题 */}
          <h1 className="text-5xl md:text-7xl font-light tracking-widest mb-16">
            <span
              ref={greetingRef as React.RefObject<HTMLSpanElement>}
              className="font-serif italic text-muted text-4xl block mb-6"
            >
              {greeting}
            </span>
            智能规划，
            <span ref={headlineRef as React.RefObject<HTMLSpanElement>} className="font-serif italic time-theme-text">
              让出行更简单。
            </span>
          </h1>

          {/* 内联输入流 */}
          <div
            ref={formRef as React.RefObject<HTMLDivElement>}
            className="text-2xl md:text-3xl font-light tracking-wide flex flex-wrap justify-center items-center gap-y-8 leading-relaxed"
          >
            <span className="text-muted">我想从</span>
            <StationInput
              value={params.origin}
              onChange={setOrigin}
              placeholder="出发地"
              aria-label="出发地"
            />
            <span className="text-muted">出发，前往</span>
            <StationInput
              value={params.destination}
              onChange={setDestination}
              placeholder="目的地"
              aria-label="目的地"
            />
            <span className="text-muted">，</span>
            <span className="text-muted w-full md:w-auto mt-4 md:mt-0">
              日期是
            </span>
            <DatePicker value={params.date} onChange={setDate} />
            <span className="text-muted">。</span>
          </div>

          {/* 生成按钮 */}
          <div className="mt-24 flex flex-col items-center gap-10">
            <button
              ref={btnRef as React.RefObject<HTMLButtonElement>}
              onClick={handleSearch}
              className="group relative rounded-full px-12 py-5 text-sm font-medium tracking-[0.2em] uppercase overflow-hidden cursor-pointer transition-colors bg-starlight text-void"
            >
              <span className="relative z-10 flex items-center gap-3">
                生成出行方案
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </span>
              <div
                className="absolute inset-0 translate-y-full group-hover:translate-y-0 transition-transform duration-500 time-theme-bg"
              />
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
