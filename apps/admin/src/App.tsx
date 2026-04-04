import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Suspense, lazy, useEffect } from 'react';
import { AdminLayout } from '@/components/layout/AdminLayout';

const OverviewView = lazy(() => import('@/pages/OverviewView'));
const TasksView = lazy(() => import('@/pages/TasksView'));
const DataView = lazy(() => import('@/pages/DataView'));
const ConfigView = lazy(() => import('@/pages/ConfigView'));
const LogView = lazy(() => import('@/pages/LogView'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 1000 * 60 * 5,
    },
  },
});

export default function App() {
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', 'dusk');
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AdminLayout />}>
            <Route index element={<Suspense fallback={null}><OverviewView /></Suspense>} />
            <Route path="tasks" element={<Suspense fallback={null}><TasksView /></Suspense>} />
            <Route path="data" element={<Suspense fallback={null}><DataView /></Suspense>} />
            <Route path="config" element={<Suspense fallback={null}><ConfigView /></Suspense>} />
            <Route path="log" element={<Suspense fallback={null}><LogView /></Suspense>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
