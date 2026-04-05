import { useTheme } from '../../context/ThemeContext';
import type { Theme } from '../../context/ThemeContext';
import './ThemeSwitcher.css';

const themes: { value: Theme; label: string; icon: string }[] = [
  { value: 'light', label: 'Light', icon: '☀️' },
  { value: 'dark', label: 'Dark Pro', icon: '🌙' },
];

interface Props {
  collapsed?: boolean;
}

export default function ThemeSwitcher({ collapsed = false }: Props) {
  const { theme, setTheme } = useTheme();

  return (
    <div className={`theme-switcher${collapsed ? ' theme-switcher--collapsed' : ''}`}>
      {themes.map((t) => (
        <button
          key={t.value}
          className={`theme-btn${theme === t.value ? ' theme-btn--active' : ''}`}
          onClick={() => setTheme(t.value)}
          title={t.label}
        >
          <span style={{ fontSize: '15px', flexShrink: 0 }}>{t.icon}</span>
          <span className="theme-btn__label">{t.label}</span>
        </button>
      ))}
    </div>
  );
}
