import type { ReactNode } from 'react';
import { Fragment, useCallback, useEffect, useState } from 'react';
import { LiveGame } from '../features/game/LiveGame';
import {
  admitGuest,
  ApiError,
  clearDeviceEnrollment,
  clearGuestSession,
  enrollDevice,
  fetchTakenAvatars,
  readDeviceEnrollment,
  readGuestSession,
} from '../features/rooms/api';
import { scoredResult } from './fixtures';
import { CheckingScreen, ResultScreen } from './screens/Finish';
import { DeviceSetupScreen, GrownupsGateScreen, ParentsScreen } from './screens/Grownups';
import { FixtureTeamScreen, MicScreen, ModeScreen, PickCharacterScreen } from './screens/JoinFlow';
import { DrawerPlayScreen, SpeakerPlayScreen } from './screens/Play';
import { MusicProvider } from './ui/frame';

function JoinRoute() {
  const [device, setDevice] = useState(readDeviceEnrollment);
  const [session, setSession] = useState(readGuestSession);
  const [justJoined, setJustJoined] = useState(false);
  const [taken, setTaken] = useState<string[]>([]);

  const forgetDevice = useCallback(() => {
    clearDeviceEnrollment();
    setDevice(null);
  }, []);
  const exitGame = useCallback(() => {
    clearGuestSession();
    setSession(null);
  }, []);

  useEffect(() => {
    if (!device || session) return;
    fetchTakenAvatars(device)
      .then(setTaken)
      .catch((error) => {
        if (error instanceof ApiError && error.code === 'device_not_enrolled') forgetDevice();
      });
  }, [device, session, forgetDevice]);

  if (session) return <LiveGame key={session.guest_session_token} session={session} startAtMic={justJoined} onExit={exitGame} />;
  if (!device) {
    return (
      <DeviceSetupScreen
        onUnlock={async (passcode) => {
          try {
            setDevice(await enrollDevice(passcode));
            return null;
          } catch (error) {
            return error instanceof ApiError ? error.message : 'That did not work. Try again.';
          }
        }}
      />
    );
  }
  return (
    <PickCharacterScreen
      takenAvatarIds={taken}
      onGo={async (nickname, avatarId) => {
        try {
          const admitted = await admitGuest(device, nickname, avatarId);
          setJustJoined(true);
          setSession(admitted);
          return null;
        } catch (error) {
          if (error instanceof ApiError && error.code === 'device_not_enrolled') forgetDevice();
          fetchTakenAvatars(device).then(setTaken).catch(() => undefined);
          return error instanceof ApiError ? error.message : 'That did not work. Try again.';
        }
      }}
    />
  );
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
