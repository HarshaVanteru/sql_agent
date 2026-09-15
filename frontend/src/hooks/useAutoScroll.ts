import { useEffect, useRef } from 'react';

/**
 * Keep a scrolling list pinned to the bottom as things are added -- unless the
 * reader has scrolled up, in which case they are reading something and yanking
 * them back down would be rude.
 */
export function useAutoScroll<T extends HTMLElement>(dependency: unknown) {
  const ref = useRef<T>(null);
  const pinned = useRef(true);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const onScroll = () => {
      const distanceFromBottom =
        element.scrollHeight - element.scrollTop - element.clientHeight;
      pinned.current = distanceFromBottom < 80;
    };

    element.addEventListener('scroll', onScroll, { passive: true });
    return () => element.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    const element = ref.current;
    if (element && pinned.current) element.scrollTop = element.scrollHeight;
  }, [dependency]);

  return ref;
}
