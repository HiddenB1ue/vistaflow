import { useTheme } from '@/hooks/useTheme';
import { usePageTransition } from '@/hooks/usePageTransition';
import { useLocation } from 'react-router-dom';

interface NavbarProps {
  onFilterOpen?: () => void;
}

export function Navbar({ onFilterOpen }: NavbarProps) {
  const { toggleTheme } = useTheme();
  const { navigateTo } = usePageTransition();
  const location = useLocation();
  const isJourney = location.pathname === '/journey';

  return (
    <nav
      className="fixed top-0 w-full p-8 md:p-12 flex justify-between items-center z-50 mix-blend-difference"
    >
      {/* Logo */}
      <div
        className="font-display font-medium text-xl tracking-[0.3em] uppercase text-white cursor-pointer"
        onClick={() => navigateTo('/')}
      >
        VistaFlow
      </div>

      <div className="flex items-center gap-8">
        {/* 面包屑：仅在 JourneyPage 显示 */}
        {isJourney && (
          <div className="flex items-center gap-3 text-xs font-display tracking-widest"
            style={{ color: 'var(--color-text-secondary)' }}
          >
            <span
              className="cursor-pointer hover:text-white transition-colors"
              onClick={() => navigateTo('/')}
            >
              首页
            </span>
            <span style={{ opacity: 0.3 }}>/</span>
            <span className="time-theme-text">出行方案</span>
          </div>
        )}

        {/* 偏好设置按钮 */}
        {onFilterOpen && (
          <button
            className="text-sm font-display tracking-widest hover:text-white text-gray-400 transition-colors flex items-center gap-2 cursor-pointer"
            onClick={onFilterOpen}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
            出行偏好
          </button>
        )}

        {/* 主题切换 */}
        <button
          onClick={toggleTheme}
          className="text-sm font-display tracking-widest text-gray-400 hover:text-white transition-colors cursor-pointer"
          aria-label="切换主题"
        >
          ◐
        </button>
      </div>
    </nav>
  );
}
