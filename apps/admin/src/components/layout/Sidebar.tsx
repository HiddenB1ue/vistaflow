
import { NavLink, useNavigate } from 'react-router-dom';
import { TopbarBrand } from '@vistaflow/ui';
import { useAuth } from '@/contexts/AuthContext';
import { SIDEBAR_LABELS } from '@/constants/labels';
import './Sidebar.css';

interface SidebarProps {
  pendingTaskCount: number;
}

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
}

const dataOpsItems: NavItem[] = [
  {
    path: '/',
    label: SIDEBAR_LABELS.overview,
    icon: (<svg className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v5a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10-1a1 1 0 011-1h4a1 1 0 011 1v6a1 1 0 01-1 1h-4a1 1 0 01-1-1v-6z" /></svg>),
  },
  {
    path: '/tasks',
    label: SIDEBAR_LABELS.tasks,
    icon: (<svg className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg>),
  },
  {
    path: '/data',
    label: SIDEBAR_LABELS.data,
    icon: (<svg className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2 1 3 3 3h10c2 0 3-1 3-3V7M4 7c0-2 1-3 3-3h10c2 0 3 1 3 3M4 7h16M9 11h6m-6 4h4" /></svg>),
  },
];

const systemItems: NavItem[] = [
  {
    path: '/config',
    label: SIDEBAR_LABELS.config,
    icon: (<svg className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>),
  },
  {
    path: '/log',
    label: SIDEBAR_LABELS.log,
    icon: (<svg className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>),
  },
];

export function Sidebar({ pendingTaskCount }: SidebarProps) {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <aside className="admin-sidebar z-20 flex w-64 shrink-0 flex-col border-r border-white/8">
      <div className="border-b border-white/5 vf-page-gutter" style={{ paddingBlock: 'var(--vf-page-gutter-y)' }}>
        <TopbarBrand type="button" logoSrc="/vistaflow-brand-mark.svg" logoAlt="">{SIDEBAR_LABELS.brand}</TopbarBrand>
      </div>

      <nav className="flex-1 overflow-y-auto py-3" style={{ scrollbarWidth: 'none' }}>
        <div className="nav-section-label">{SIDEBAR_LABELS.dataOps}</div>
        {dataOpsItems.map((item) => (
          <NavLink key={item.path} to={item.path} end={item.path === '/'} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            {item.icon}
            {item.label}
            {item.path === '/tasks' && pendingTaskCount > 0 && (
              <span className="ml-auto rounded border border-[#FACC15]/25 bg-[#FACC15]/15 px-1.5 py-0.5 font-display text-[10px] text-[#FACC15]">{pendingTaskCount}</span>
            )}
          </NavLink>
        ))}

        <div className="nav-section-label mt-3">{SIDEBAR_LABELS.system}</div>
        {systemItems.map((item) => (
          <NavLink key={item.path} to={item.path} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            {item.icon}
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-white/5 p-4">
        <div className="flex items-center gap-3 rounded-lg bg-white/3 px-3 py-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-[#8B5CF6] to-[#6D28D9] text-xs font-display font-medium">A</div>
          <div>
            <div className="text-xs font-medium text-starlight">{SIDEBAR_LABELS.adminName}</div>
            <div className="text-[10px] text-muted">{SIDEBAR_LABELS.adminRole}</div>
          </div>
          <button
            onClick={handleLogout}
            className="ml-auto h-4 w-4 cursor-pointer text-muted transition-colors hover:text-white"
            title="退出登录"
            aria-label="退出登录"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>
    </aside>
  );
}
