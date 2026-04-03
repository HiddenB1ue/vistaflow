import { useTheme as useSharedTheme } from '@vistaflow/utils';
import { useUiStore } from '@/stores/uiStore';

export function useTheme() {
  const theme = useUiStore((s) => s.theme);
  const setTheme = useUiStore((s) => s.setTheme);

  return useSharedTheme({
    getTheme: () => theme,
    setTheme: (t: string) => setTheme(t as typeof theme),
  });
}
