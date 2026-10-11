import { useSyncExternalStore } from 'react';

const PHONE_MAX_WIDTH = 600;

function subscribeToResize(onChange: () => void) {
  window.addEventListener('resize', onChange);
  return () => window.removeEventListener('resize', onChange);
}

/** True on phone-width screens, which drop controls the iPhone designs leave out. */
export function useIsPhone(): boolean {
  return useSyncExternalStore(subscribeToResize, () => window.innerWidth < PHONE_MAX_WIDTH);
}
