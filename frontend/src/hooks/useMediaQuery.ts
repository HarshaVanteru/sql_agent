import { useEffect, useState } from 'react';

/**
 * Whether a CSS media query currently matches.
 *
 * For the handful of decisions CSS cannot make on its own -- an attribute like
 * `aria-hidden` or `inert` is either set or not, and no breakpoint can help.
 * Layout stays in CSS; this is only for what has to be a value in the DOM.
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() =>
    typeof window === 'undefined' ? false : window.matchMedia(query).matches,
  );

  useEffect(() => {
    const list = window.matchMedia(query);
    const onChange = () => setMatches(list.matches);
    onChange();
    list.addEventListener('change', onChange);
    return () => list.removeEventListener('change', onChange);
  }, [query]);

  return matches;
}
