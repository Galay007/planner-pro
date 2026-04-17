import { Calendar, DatabaseBackup, CalendarSync, Link2, Activity } from "lucide-react";
import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import ThemeSwitcher from './ThemeSwitcher';
import './Sidebar.css';

const navItems = [
  { to: '/', label: 'Планировщик', icon: Calendar },
  { to: '/connections', label: 'Подключения', icon: Link2 },
  { to: '/migration-db', label: 'Миграция БД', icon: DatabaseBackup },
  { to: '/migration-csv', label: 'Миграция CSV', icon: CalendarSync },
  { to: '/monitoring', label: 'Мониторинг', icon: Activity },
];

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
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `sidebar__link${isActive ? ' sidebar__link--active' : ''}`
            }
            title={collapsed ? item.label : undefined}
          >
            <item.icon size={22}  />
            <span className="sidebar__label">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <ThemeSwitcher collapsed={collapsed} />
    </aside>
  );
}
