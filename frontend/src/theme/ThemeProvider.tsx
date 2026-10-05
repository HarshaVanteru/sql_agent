import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

export type ThemePreference = 'light' | 'dark' | 'system';
export type ResolvedTheme = 'light' | 'dark';

const STORAGE_KEY = 'theme';
const DARK_QUERY = '(prefers-color-scheme: dark)';

interface ThemeContextValue {
  /** What the visitor chose; "system" means follow the OS. */
  preference: ThemePreference;
  /** What is actually on screen. */
  resolved: ResolvedTheme;
  setPreference: (preference: ThemePreference) => void;
  /** Flip between light and dark, leaving "system" behind. */
  toggle: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function readPreference(): ThemePreference {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'light' || stored === 'dark' || stored === 'system') return stored;
  } catch {
    // Storage can be blocked; fall through to following the system.
  }
  return 'system';
}

function systemTheme(): ResolvedTheme {
  return window.matchMedia(DARK_QUERY).matches ? 'dark' : 'light';
}

function apply(theme: ResolvedTheme) {
  const root = document.documentElement;
  root.dataset.theme = theme;
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute('content', theme === 'dark' ? '#101412' : '#FAF9F6');
}

/**
 * Owns the theme. index.html sets `data-theme` before first paint so there is
 * no flash; this keeps it in step afterwards and follows the OS while the
 * preference is "system".
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  const [preference, setPreferenceState] = useState<ThemePreference>(readPreference);
  const [system, setSystem] = useState<ResolvedTheme>(systemTheme);

  useEffect(() => {
    const list = window.matchMedia(DARK_QUERY);
    const onChange = () => setSystem(list.matches ? 'dark' : 'light');
    list.addEventListener('change', onChange);
    return () => list.removeEventListener('change', onChange);
  }, []);

  const resolved: ResolvedTheme = preference === 'system' ? system : preference;

  useEffect(() => apply(resolved), [resolved]);

  // Keep several open tabs in agreement.
  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key === STORAGE_KEY) setPreferenceState(readPreference());
    };
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  const setPreference = useCallback((next: ThemePreference) => {
    setPreferenceState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Not persisted; still applies for this visit.
    }
  }, []);

  const toggle = useCallback(
    () => setPreference(resolved === 'dark' ? 'light' : 'dark'),
    [resolved, setPreference],
  );

  const value = useMemo(
    () => ({ preference, resolved, setPreference, toggle }),
    [preference, resolved, setPreference, toggle],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used inside <ThemeProvider>.');
  return ctx;
}
