
import { useLocation } from 'react-router-dom';
import { Topbar, TopbarActions, TopbarBrand } from '@vistaflow/ui';
import { NAVBAR_LABELS } from '@/constants/labels';
import { useTheme } from '@/hooks/useTheme';
import { usePageTransition } from '@/hooks/usePageTransition';

interface NavbarProps {
  onFilterOpen?: () => void;
}

export function Navbar({ onFilterOpen }: NavbarProps) {
  const { theme, toggleTheme } = useTheme();
  const { navigateTo } = usePageTransition();
  const location = useLocation();
  const isJourney = location.pathname === '/journey';

  return (
    <Topbar blendMode="difference" className="z-50">
      <TopbarBrand logoSrc="/vistaflow-brand-mark.svg" logoAlt="" onClick={() => navigateTo('/')}>{NAVBAR_LABELS.brand}</TopbarBrand>

      <TopbarActions className="gap-4 md:gap-8">
        {isJourney && (
          <div
            className="hidden items-center gap-3 text-xs font-display tracking-[0.18em] md:flex"
            style={{ color: 'var(--color-text-secondary)' }}
          >
            <button
              type="button"
              className="cursor-pointer transition-colors hover:text-white"
              onClick={() => navigateTo('/')}
            >
              {NAVBAR_LABELS.home}
            </button>
            <span style={{ opacity: 0.3 }}>/</span>
            <span className="time-theme-text">{NAVBAR_LABELS.journeyPlan}</span>
          </div>
        )}

        {onFilterOpen && (
          <button
            type="button"
            className="flex cursor-pointer items-center gap-2 text-sm font-display tracking-[0.18em] text-gray-400 transition-colors hover:text-white"
            onClick={onFilterOpen}
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
            {NAVBAR_LABELS.filterButton}
          </button>
        )}

        <button
          type="button"
          onClick={toggleTheme}
          className="cursor-pointer text-sm font-display tracking-[0.18em] text-gray-400 transition-colors hover:text-white"
          aria-label={NAVBAR_LABELS.themeToggle}
          title={NAVBAR_LABELS.themeToggle}
        >
          {theme === 'dawn' ? (
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M21 12.8A9 9 0 1111.2 3 7 7 0 0021 12.8z" />
            </svg>
          ) : (
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="12" r="4" strokeWidth="1.8" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 2v2m0 16v2m10-10h-2M4 12H2m17.07 7.07l-1.41-1.41M6.34 6.34 4.93 4.93m14.14 0-1.41 1.41M6.34 17.66l-1.41 1.41" />
            </svg>
          )}
        </button>
      </TopbarActions>
    </Topbar>
  );
}
