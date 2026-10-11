import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';
import { avatarAssets, drawyAssets } from './assets';
import { characterOptions, drawerSnapshot, palette, speakerSnapshot } from './fixtures';
import { readGuestSession } from '../features/rooms/api';
import { RoomPanel } from '../features/rooms/RoomPanel';

const routes = [
  { path: '/join', label: 'Character' },
  { path: '/mic', label: 'Mic' },
  { path: '/mode', label: 'Mode' },
  { path: '/team', label: 'Team' },
  { path: '/intro', label: 'Intro' },
  { path: '/play/speaker', label: 'Speaker' },
  { path: '/play/drawer', label: 'Drawer' },
  { path: '/checking', label: 'Checking' },
  { path: '/result', label: 'Result' },
] as const;

type RoutePath = (typeof routes)[number]['path'];
type AppPath = RoutePath | '/grownups';

function currentPath(): AppPath {
  const path = window.location.pathname;
  if (path === '/grownups') return path;
  return routes.some((route) => route.path === path) ? (path as RoutePath) : '/join';
}

function RouteNav({ activePath }: { activePath: RoutePath }) {
  return (
    <nav className="flow-nav" aria-label="Fixture screen flow">
      {routes.map((route) => (
        <a key={route.path} href={route.path} aria-current={activePath === route.path ? 'page' : undefined}>
          {route.label}
        </a>
      ))}
    </nav>
  );
}

function Mascot({ pose, alt }: { pose: keyof typeof drawyAssets; alt: string }) {
  return <img className="drawy" src={drawyAssets[pose]} alt={alt} />;
}

function AppFrame({ children, activePath }: { children: ReactNode; activePath: RoutePath }) {
  return (
    <main className="app-shell">
      <div className="sky-scene" aria-hidden="true">
        <span className="cloud cloud-one" />
        <span className="cloud cloud-two" />
        <span className="hill hill-back" />
        <span className="hill hill-front" />
      </div>
      <RouteNav activePath={activePath} />
      {children}
      <p className="fixture-note">{activePath === '/join'
        ? 'Private matching works for admitted guests. No Room join flow is configured; other screens are fixture previews.'
        : 'Fixture preview only. No live voice, drawing relay, object delivery, or AI yet.'}</p>
    </main>
  );
}

function JoinScreen() {
  const [selected, setSelected] = useState('mango');
  const [session] = useState(readGuestSession);

  return (
    <section className="screen-card join-screen" data-session={Boolean(session)} aria-labelledby="join-title">
      <div className="screen-copy">
        <Mascot pose="curious" alt="Drawy holding a crayon" />
        <h1 id="join-title">{session ? 'Your team' : 'Pick your character'}</h1>
        {session ? <RoomPanel key={session.guest_session_token} session={session} /> : (
          <>
            <label className="name-field">
              My name
              <input defaultValue="Mango" aria-label="My name" />
            </label>
            <p className="join-message">Room admission is not configured. Character selection below is a preview.</p>
          </>
        )}
      </div>
      {!session && <div className="avatar-grid" aria-label="Choose one avatar">
        {characterOptions.map((character) => {
          return (
            <button
              className="avatar-choice"
              data-selected={selected === character.id}
              key={character.id}
              onClick={() => setSelected(character.id)}
              type="button"
            >
              <img src={avatarAssets[character.id]} alt="" />
              <span>{character.name}</span>
            </button>
          );
        })}
      </div>}
      <div className="action-row">
        <a className="secondary-button" href="/grownups">
          Grown-ups
        </a>
        <a className="primary-button" href="/mic">
          Preview screens
        </a>
      </div>
    </section>
  );
}

function MicScreen() {
  return (
    <section className="screen-card split-card" aria-labelledby="mic-title">
      <Mascot pose="listen" alt="Drawy listening" />
      <div className="screen-copy">
        <h1 id="mic-title">Turn on your mic</h1>
        <p>A grown-up can tap Allow. Your mic only sends sound when you hold the talk button later.</p>
        <div className="permission-card">
          <span className="mic-dot" />
          Browser permission is not requested in this fixture.
        </div>
        <div className="action-row left">
          <a className="secondary-button" href="/join">
            Back
          </a>
          <a className="primary-button coral" href="/mode">
            I understand
          </a>
        </div>
      </div>
    </section>
  );
}

function ModeScreen() {
  return (
    <section className="screen-card split-card" aria-labelledby="mode-title">
      <Mascot pose="talk" alt="Drawy ready to play" />
      <div className="screen-copy">
        <h1 id="mode-title">Pick a picture mode</h1>
        <div className="mode-grid">
          <a className="mode-card selected" href="/team">
            <strong>Normal</strong>
            <span>Big, friendly pictures for the demo.</span>
          </a>
          <button className="mode-card" disabled type="button">
            <strong>Advanced</strong>
            <span>Advanced pictures are coming soon!</span>
          </button>
        </div>
      </div>
    </section>
  );
}

function TeamScreen() {
  const teammate = drawerSnapshot.room.teammate;

  return (
    <section className="screen-card team-screen" aria-labelledby="team-title">
      <Mascot pose="cheer" alt="Drawy cheering" />
      <h1 id="team-title">You and {teammate?.nickname} are a team!</h1>
      <div className="team-pair">
        <AvatarBadge avatarId="mango" label="You" />
        <span className="team-plus">+</span>
        <AvatarBadge avatarId="kiwi" label={teammate?.nickname ?? 'Waiting'} />
      </div>
      <p className="waiting-copy">Roles come from the room state. Bot partners are not part of this fixture.</p>
      <a className="primary-button" href="/intro">
        Let's play
      </a>
    </section>
  );
}

function AvatarBadge({ avatarId, label }: { avatarId: keyof typeof avatarAssets; label: string }) {
  return (
    <figure className="avatar-badge">
      <img src={avatarAssets[avatarId]} alt="" />
      <figcaption>{label}</figcaption>
    </figure>
  );
}

function IntroScreen() {
  return (
    <section className="screen-card role-intro" aria-labelledby="intro-title">
      <Mascot pose="talk" alt="Drawy talking" />
      <p className="role-chip talk">You talk</p>
      <h1 id="intro-title">Tell Mango what you see</h1>
      <p>Use shapes, colors, and parts. Do not say the picture name.</p>
      <a className="primary-button coral" href="/play/speaker">
        Start talking
      </a>
    </section>
  );
}

function TopBar({ role }: { role: 'talk' | 'draw' }) {
  return (
    <header className="play-topbar">
      <button className="round-icon" type="button" aria-label="Music control disabled in fixture">
        ♪
      </button>
      <span className={`role-chip ${role}`}>You {role}</span>
      <span className="time-pill">Time fixture</span>
    </header>
  );
}

function SpeakerPlayScreen() {
  const teammate = speakerSnapshot.room.teammate?.nickname ?? 'teammate';

  return (
    <section className="play-screen" aria-labelledby="speaker-title">
      <h1 className="sr-only" id="speaker-title">Speaker play fixture</h1>
      <TopBar role="talk" />
      <div className="play-grid speaker-grid">
        <article className="photo-card">
          <p className="card-title">Photo</p>
          <div className="object-placeholder" aria-label="Authorized Speaker object placeholder">
            <span>3D</span>
            <strong>Secret picture slot</strong>
            <small>Only the Speaker view may use this area before Reveal.</small>
          </div>
          <div className="tool-row" aria-label="Viewer controls not wired yet">
            <button type="button">Rotate</button>
            <button type="button">Zoom</button>
            <button type="button">Reset</button>
          </div>
        </article>
        <article className="live-card">
          <p className="card-title"><span className="live-dot" /> {teammate}'s drawing</p>
          <DrawingPreview readonly />
          <SpeakingBars label={`${teammate} is talking`} />
        </article>
      </div>
      <HoldButton />
    </section>
  );
}

function DrawerPlayScreen() {
  return (
    <section className="play-screen drawer-play" aria-labelledby="drawer-title">
      <TopBar role="draw" />
      <SpeakingBars label="Kiwi is talking" />
      <div className="canvas-card">
        <h1 id="drawer-title">Draw what you hear</h1>
        <DrawingPreview />
        <div className="palette" aria-label="Drawing colors fixture">
          {palette.map((color) => (
            <button key={color} style={{ background: color }} type="button" aria-label={`Color ${color}`} />
          ))}
        </div>
        <div className="tool-row">
          <button type="button">Undo</button>
          <button type="button">Clear</button>
        </div>
      </div>
      <div className="drawer-actions">
        <HoldButton />
        <a className="primary-button mint" href="/checking">
          Done!
        </a>
      </div>
    </section>
  );
}

function DrawingPreview({ readonly = false }: { readonly?: boolean }) {
  return (
    <div className="drawing-preview" data-readonly={readonly} aria-label={readonly ? 'Read-only drawing preview' : 'Drawing canvas placeholder'}>
      <svg viewBox="0 0 320 220" role="img" aria-label="Fixture strokes">
        <path d="M80 132 C120 84 188 88 224 132" />
        <path d="M100 142 C132 178 188 178 218 142" />
        <circle cx="155" cy="126" r="18" />
      </svg>
      <span>{readonly ? 'Read-only live frame' : 'Canvas shell'}</span>
    </div>
  );
}

function SpeakingBars({ label }: { label: string }) {
  return (
    <div className="speaking-bars" aria-label={label}>
      <span />
      <span />
      <span />
      <span />
    </div>
  );
}

function HoldButton() {
  return (
    <button className="hold-button" type="button" aria-label="Hold to talk fixture only">
      Hold to talk
      <small>No audio publishes in this fixture</small>
    </button>
  );
}

function CheckingScreen() {
  return (
    <section className="screen-card checking-screen" aria-labelledby="checking-title">
      <Mascot pose="search" alt="Drawy checking the drawing" />
      <div className="screen-copy">
        <h1 id="checking-title">Drawy is checking</h1>
        <p>Talking and drawing are paused now. If checking takes too long, the round can still finish safely.</p>
        <div className="checking-panel" aria-label="Finalizing fixture state">
          <span />
          <strong>Finalizing fixture</strong>
          <small>No AI score is running in this demo shell.</small>
        </div>
        <div className="action-row left">
          <a className="secondary-button" href="/play/drawer">
            Back to drawer shell
          </a>
          <a className="primary-button" href="/result">
            See result fixture
          </a>
        </div>
      </div>
    </section>
  );
}

function ResultScreen() {
  return (
    <section className="screen-card result-screen" aria-labelledby="result-title">
      <div className="result-hero">
        <Mascot pose="cheer" alt="Drawy celebrating" />
        <div>
          <p className="result-badge">Team result</p>
          <h1 id="result-title">You finished together!</h1>
          <p>Drawy had trouble checking this one, but you still finished the round together!</p>
        </div>
      </div>
      <div className="result-grid">
        <article className="comparison-card">
          <p className="card-title">Your drawing</p>
          <DrawingPreview readonly />
        </article>
        <article className="comparison-card reference-after-reveal">
          <p className="card-title">Picture after Reveal</p>
          <div className="reward-object" aria-label="Discovery Reward fixture">
            <span>3D</span>
            <strong>Discovery Reward</strong>
            <small>Available every round, even without a score.</small>
          </div>
        </article>
      </div>
      <div className="feedback-card">
        <strong>Drawy says</strong>
        <p>You listened for the big shape.</p>
        <p>Let's look at the picture and try another one.</p>
      </div>
      <div className="action-row">
        <a className="secondary-button" href="/join">
          Done
        </a>
        <a className="primary-button mint" href="/intro">
          Play again
        </a>
      </div>
    </section>
  );
}

function GrownupsScreen() {
  return (
    <section className="screen-card grownups-screen" aria-labelledby="grownups-title">
      <div className="phone-gate">
        <Mascot pose="curious" alt="Drawy at a gate" />
        <h1 id="grownups-title">Grown-ups gate</h1>
        <p>Real grown-up access is blocked until separate authorization is designed.</p>
        <div className="lock-card" aria-label="Blocked grown-up access">
          <span>Lock</span>
          <strong>No parent metrics or host controls are available in this child fixture.</strong>
        </div>
        <a className="secondary-button" href="/join">
          Back to child flow
        </a>
      </div>
    </section>
  );
}

export function App() {
  const [activePath, setActivePath] = useState<AppPath>(currentPath);

  useEffect(() => {
    const onClick = (event: MouseEvent) => {
      const link = (event.target as HTMLElement).closest('a[href^="/"]');
      if (!link) return;
      const href = link.getAttribute('href');
      if (!href) return;
      event.preventDefault();
      window.history.pushState({}, '', href);
      setActivePath(currentPath());
    };
    const onPopState = () => setActivePath(currentPath());
    document.addEventListener('click', onClick);
    window.addEventListener('popstate', onPopState);
    return () => {
      document.removeEventListener('click', onClick);
      window.removeEventListener('popstate', onPopState);
    };
  }, []);

  if (activePath === '/grownups') {
    return (
      <AppFrame activePath="/join">
        <GrownupsScreen />
      </AppFrame>
    );
  }

  const screen = {
    '/join': <JoinScreen />,
    '/mic': <MicScreen />,
    '/mode': <ModeScreen />,
    '/team': <TeamScreen />,
    '/intro': <IntroScreen />,
    '/play/speaker': <SpeakerPlayScreen />,
    '/play/drawer': <DrawerPlayScreen />,
    '/checking': <CheckingScreen />,
    '/result': <ResultScreen />,
  }[activePath];

  return <AppFrame activePath={activePath}>{screen}</AppFrame>;
}
