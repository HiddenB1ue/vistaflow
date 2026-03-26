import { useEffect } from 'react';
import { useUiStore } from '@/stores/uiStore';
import type { Theme } from '@/types/theme';

export function useTheme() {
  const theme = useUiStore((s) => s.theme);
  const setTheme = useUiStore((s) => s.setTheme);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(theme === 'dawn' ? 'dusk' : 'dawn');
  };

  const applyTheme = (t: Theme) => setTheme(t);

  return { theme, toggleTheme, applyTheme };
}
