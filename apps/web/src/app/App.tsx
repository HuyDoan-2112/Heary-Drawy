import type { ReactNode } from 'react';
import { Fragment, useEffect, useState } from 'react';
import { readGuestSession } from '../features/rooms/api';
import { RoomPanel } from '../features/rooms/RoomPanel';
import { scoredResult } from './fixtures';
import { CheckingScreen, ResultScreen } from './screens/Finish';
import { GrownupsGateScreen, ParentsScreen } from './screens/Grownups';
import { FixtureTeamScreen, MicScreen, ModeScreen, PickCharacterScreen } from './screens/JoinFlow';
import { DrawerPlayScreen, SpeakerPlayScreen } from './screens/Play';
import { MusicProvider } from './ui/frame';

function JoinRoute() {
  const [session] = useState(readGuestSession);
  return session ? <RoomPanel key={session.guest_session_token} session={session} /> : <PickCharacterScreen />;
}

const routes: Record<string, () => ReactNode> = {
  '/join': () => <JoinRoute />,
  '/mic': () => <MicScreen />,
  '/mode': () => <ModeScreen />,
  '/team': () => <FixtureTeamScreen />,
  '/play/speaker': () => <SpeakerPlayScreen />,
  '/play/drawer': () => <DrawerPlayScreen />,
  '/checking': () => <CheckingScreen />,
  '/result': () => <ResultScreen result={scoredResult} />,
  '/grownups': () => <GrownupsGateScreen />,
  '/grownups/parents': () => <ParentsScreen />,
};

function currentPath(): string {
  const path = window.location.pathname;
  return Object.hasOwn(routes, path) ? path : '/join';
}

export function App() {
  const [path, setPath] = useState(currentPath);

  useEffect(() => {
    const onClick = (event: MouseEvent) => {
      const link = (event.target as HTMLElement).closest('a[href^="/"]');
      const href = link?.getAttribute('href');
      if (!href) return;
      event.preventDefault();
      window.history.pushState({}, '', href);
      setPath(currentPath());
    };
    const onPopState = () => setPath(currentPath());
    document.addEventListener('click', onClick);
    window.addEventListener('popstate', onPopState);
    return () => {
      document.removeEventListener('click', onClick);
      window.removeEventListener('popstate', onPopState);
    };
  }, []);

  // Keyed by path so each screen starts fresh (the role intro replays, drawings reset).
  return <MusicProvider><Fragment key={path}>{routes[path]()}</Fragment></MusicProvider>;
}
