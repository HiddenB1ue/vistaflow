import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect } from 'react';
import { AppLayout } from '@/components/layout/AppLayout';
import { SearchPage } from '@/pages/SearchPage';
import { JourneyPage } from '@/pages/JourneyPage';
import { useTheme } from '@/hooks/useTheme';
import { stationCache } from '@/services/stationCache';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 1000 * 60 * 5,
    },
  },
});

function ThemeInitializer({ children }: { children: React.ReactNode }) {
  useTheme();

  // 预加载车站数据
  useEffect(() => {
    stationCache.ensureLoaded().catch((error) => {
      console.error('预加载车站数据失败:', error);
    });
  }, []);

  return <>{children}</>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeInitializer>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/" element={<SearchPage />} />
              <Route path="/journey" element={<JourneyPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </ThemeInitializer>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
