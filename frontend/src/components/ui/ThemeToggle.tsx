import { MoonIcon } from '@/components/icons/MoonIcon';
import { SunIcon } from '@/components/icons/SunIcon';
import { useTheme } from '@/theme/ThemeProvider';
import { IconButton } from './IconButton';

/** Shows where a click goes next: the moon in light mode, the sun in dark. */
export function ThemeToggle({ className }: { className?: string }) {
  const { resolved, toggle } = useTheme();
  const dark = resolved === 'dark';
  return (
    <IconButton
      label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
      onClick={toggle}
      className={className}
    >
      {dark ? <SunIcon /> : <MoonIcon />}
    </IconButton>
  );
}
