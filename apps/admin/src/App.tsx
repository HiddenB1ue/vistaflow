import { useEffect } from 'react';
import { AdminLayout } from '@/components/layout/AdminLayout';

export default function App() {
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', 'dusk');
  }, []);

  return <AdminLayout />;
}
