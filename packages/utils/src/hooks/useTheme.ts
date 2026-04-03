import { useEffect, useCallback } from 'react';

export interface UseThemeOptions {
  getTheme: () => string;
  setTheme: (theme: string) => void;
}

export function useTheme(options: UseThemeOptions) {
  const { getTheme, setTheme } = options;
  const theme = getTheme();

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme(theme === 'dawn' ? 'dusk' : 'dawn');
  }, [theme, setTheme]);

  const applyTheme = useCallback((t: string) => setTheme(t), [setTheme]);

  return { theme, toggleTheme, applyTheme };
}
