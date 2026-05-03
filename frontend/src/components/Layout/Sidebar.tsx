import { Calendar, DatabaseBackup, CalendarSync, Link2, Activity } from "lucide-react";
import { startTransition, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import ThemeSwitcher from './ThemeSwitcher';
import './Sidebar.css';

const navItems = [
  { to: '/', label: 'Планировщик', icon: Calendar, end: true },
  { to: '/connections', label: 'Подключения', icon: Link2, end: false },
  { to: '/migration-db', label: 'Миграция БД', icon: DatabaseBackup, end: false },
  { to: '/migration-csv', label: 'Миграция CSV', icon: CalendarSync, end: false },
  { to: '/monitoring', label: 'Мониторинг', icon: Activity, end: false },
];

function NavItem({ to, label, icon: Icon, end, collapsed }: {
  to: string; label: string; icon: React.ComponentType<{ size: number }>;
  end: boolean; collapsed: boolean;
}) {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const isActive = end ? pathname === to : pathname.startsWith(to);
  return (
    <button
      className={`sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
      title={collapsed ? label : undefined}
      onClick={() => startTransition(() => navigate(to))}
    >
      <Icon size={22} />
      <span className="sidebar__label">{label}</span>
    </button>
  );
}

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(
    () => localStorage.getItem('sidebar-collapsed') === 'true'
  );

  function toggle() {
    setCollapsed((prev) => {
      localStorage.setItem('sidebar-collapsed', String(!prev));
      return !prev;
    });
  }

  return (
    <aside className={`sidebar${collapsed ? ' sidebar--collapsed' : ''}`}>
      <div className="sidebar__header">
        <span className="sidebar__title">ОРКЕСТРАТОР</span>
        <button className="sidebar__toggle" onClick={toggle} title={collapsed ? 'Развернуть' : 'Свернуть'}>
          {collapsed ? '››' : '‹‹'}
        </button>
      </div>

      <nav className="sidebar__nav">
        {navItems.map((item) => (
          <NavItem
            key={item.to}
            to={item.to}
            label={item.label}
            icon={item.icon}
            end={item.end}
            collapsed={collapsed}
          />
        ))}
      </nav>

      <ThemeSwitcher collapsed={collapsed} />
    </aside>
  );
}
