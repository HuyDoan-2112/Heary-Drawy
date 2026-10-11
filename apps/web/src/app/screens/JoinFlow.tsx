import type { CSSProperties, ReactNode } from 'react';
import { useState } from 'react';
import { characterOptions, type AvatarId } from '../fixtures';
import { Avatar, Clouds, Drawy, MusicButton, Page } from '../ui/frame';
import { ArrowIcon, CheckIcon, KeyboardIcon, LockIcon, MicIcon, StarIcon } from '../ui/icons';

export function BigLink({ href, icon, children }: { href: string; icon: ReactNode; children: ReactNode }) {
  return (
    <a className="big-button" href={href}>
      {icon}
      {children}
    </a>
  );
}

/** The bottom action: a real button in the live game, a link between fixture previews. */
function NextButton({ onClick, href, icon, children, disabled = false }: {
  onClick?: () => void;
  href: string;
  icon: ReactNode;
  children: ReactNode;
  disabled?: boolean;
}) {
  if (!onClick) return <BigLink href={href} icon={icon}>{children}</BigLink>;
  return (
    <button type="button" className="big-button" onClick={onClick} disabled={disabled}>
      {icon}
      {children}
    </button>
  );
}

export interface PickCharacterProps {
  /** Characters other children in the Room already use. */
  takenAvatarIds?: string[];
  /** Joins the Room; resolves with a child-friendly error message when it did not work. */
  onGo?: (nickname: string, avatarId: AvatarId) => Promise<string | null>;
}

export function PickCharacterScreen({ takenAvatarIds, onGo }: PickCharacterProps = {}) {
  const isTaken = (id: AvatarId) =>
    takenAvatarIds ? takenAvatarIds.includes(id) : Boolean(characterOptions.find((c) => c.id === id)?.pickedBy);
  const [selected, setSelected] = useState<AvatarId | null>(null);
  const [nickname, setNickname] = useState('');
  const [error, setError] = useState('');
  const [joining, setJoining] = useState(false);
  const firstFree = characterOptions.find((character) => !isTaken(character.id))?.id ?? null;
  const current = selected && !isTaken(selected) ? selected : firstFree;

  const go = async () => {
    if (!onGo || !current || joining) return;
    setJoining(true);
    setError((await onGo(nickname, current)) ?? '');
    setJoining(false);
  };

  return (
    <Page hills className="pick-page">
      <Clouds />
      <div className="page-top">
        <MusicButton />
        <a className="grownups-link" href="/grownups">
          <LockIcon />
          Grown-ups
        </a>
      </div>
      <Drawy pose="curiousMirrored" className="pick-drawy bob" />
      <h1 className="page-title pick-title">Who are you?</h1>
      <div className="character-grid">
        {characterOptions.map((character, index) => {
          const picked = isTaken(character.id);
          return (
            <button
              key={character.id}
              type="button"
              className="character-tile"
              // Each character idles at its own rhythm (see .character-tile in styles.css).
              style={{ '--i': index } as CSSProperties}
              data-selected={current === character.id}
              data-picked={picked}
              aria-label={picked ? `${character.name}, a friend already picked this` : `I am ${character.name}`}
              aria-pressed={picked ? undefined : current === character.id}
              aria-disabled={picked || undefined}
              onClick={() => {
                if (!picked) setSelected(character.id);
              }}
            >
              <Avatar id={character.id} className="tile-avatar" />
              <span className="character-name">{character.name}</span>
              {picked ? <span className="picked-badge">Picked</span> : null}
            </button>
          );
        })}
      </div>
      <div className="page-bottom">
        <label className="name-field">
          <KeyboardIcon strokeWidth={2.2} />
          <input
            aria-label="My name, optional"
            placeholder="My name (optional)"
            autoComplete="off"
            maxLength={24}
            value={nickname}
            onChange={(event) => setNickname(event.target.value)}
          />
        </label>
        {error ? <p className="join-error" role="alert">{error}</p> : null}
        <NextButton onClick={onGo ? go : undefined} href="/mic" icon={<ArrowIcon strokeWidth={2.6} />} disabled={joining || !current}>
          Go!
        </NextButton>
      </div>
    </Page>
  );
}

export function MicScreen({ onContinue }: { onContinue?: () => void } = {}) {
  return (
    <Page hills className="mic-page">
      <Clouds />
      <div className="page-top">
        <MusicButton />
      </div>
      <div className="mic-scene">
        <Drawy pose="listen" className="mic-drawy bob" />
        <div className="mic-hero" aria-hidden="true">
          <span className="mic-ring" />
          <span className="mic-disc"><MicIcon strokeWidth={1.9} /></span>
        </div>
      </div>
      <h1 className="page-title mic-title">Can we hear you?</h1>
      <p className="mic-copy">
        Grown-up: tap <b>Allow</b> when the phone asks. Your child&apos;s voice goes live to their teammate. It is turned into
        text for Drawy&apos;s feedback and is not saved as audio.
      </p>
      <div className="page-bottom">
        <NextButton onClick={onContinue} href="/mode" icon={<MicIcon strokeWidth={2.2} />}>Turn on mic</NextButton>
      </div>
    </Page>
  );
}

function ModeStars({ filled }: { filled: number }) {
  return (
    <span className="mode-stars">
      {[0, 1, 2].map((index) => <StarIcon key={index} filled={index < filled} />)}
    </span>
  );
}

export function ModeScreen({ onContinue }: { onContinue?: () => void } = {}) {
  return (
    <Page hills className="mode-page">
      <Clouds />
      <div className="page-top">
        <MusicButton />
      </div>
      <h1 className="page-title mode-title">Pick a game!</h1>
      <div className="mode-list">
        <button type="button" className="mode-card" data-selected="true" aria-pressed="true" aria-label="Normal">
          <span className="mode-check"><CheckIcon strokeWidth={3.4} /></span>
          <svg className="mode-art" viewBox="0 0 200 200" aria-hidden="true">
            <circle cx="100" cy="104" r="92" fill="#E8FBF3" />
            <path d="M100 56C78 38 36 48 32 98c-4 52 32 90 54 86 8-2 10-5 14-5s6 3 14 5c22 4 58-34 54-86-4-50-46-60-68-42z" fill="#E5483D" stroke="#1B2B4B" strokeWidth="6" strokeLinejoin="round" />
            <path d="M100 56c0-14 4-26 12-36" fill="none" stroke="#8B5A2B" strokeWidth="7" strokeLinecap="round" />
            <path d="M112 34c10-14 30-16 42-8-6 14-26 22-42 8z" fill="#35B26B" stroke="#1B2B4B" strokeWidth="5" strokeLinejoin="round" />
          </svg>
          <span className="mode-text">
            <span className="mode-name">Normal</span>
            <ModeStars filled={1} />
          </span>
        </button>
        {/* Visible but unavailable for now; advanced content is designed later. */}
        <button type="button" className="mode-card" aria-disabled="true" aria-label="Advanced. Advanced pictures are coming soon!">
          <svg className="mode-art" viewBox="0 0 200 200" aria-hidden="true">
            <circle cx="100" cy="104" r="92" fill="#FFF3C4" />
            <circle cx="152" cy="52" r="18" fill="#FFC83D" stroke="#1B2B4B" strokeWidth="4" />
            <path d="M152 22v-8M152 90v-8M122 52h-8M190 52h-8M131 31l-6-6M179 79l-6-6M173 31l6-6" stroke="#1B2B4B" strokeWidth="4" strokeLinecap="round" />
            <rect x="60" y="96" width="78" height="66" fill="#7CC8FF" stroke="#1B2B4B" strokeWidth="5" strokeLinejoin="round" />
            <path d="M50 100 L99 58 L148 100 Z" fill="#FF6F59" stroke="#1B2B4B" strokeWidth="5" strokeLinejoin="round" />
            <rect x="118" y="62" width="12" height="22" fill="#FF6F59" stroke="#1B2B4B" strokeWidth="4" />
            <rect x="90" y="124" width="20" height="38" rx="3" fill="#8B5A2B" stroke="#1B2B4B" strokeWidth="4" />
            <rect x="68" y="108" width="16" height="16" fill="#fff" stroke="#1B2B4B" strokeWidth="4" />
            <rect x="116" y="108" width="16" height="16" fill="#fff" stroke="#1B2B4B" strokeWidth="4" />
            <rect x="30" y="128" width="9" height="34" fill="#8B5A2B" stroke="#1B2B4B" strokeWidth="4" />
            <circle cx="34" cy="116" r="20" fill="#35B26B" stroke="#1B2B4B" strokeWidth="4" />
            <path d="M18 162 H182" stroke="#1B2B4B" strokeWidth="5" strokeLinecap="round" />
          </svg>
          <span className="mode-text">
            <span className="mode-name">Advanced</span>
            <ModeStars filled={3} />
          </span>
        </button>
        <Drawy pose="talk" className="mode-drawy bob" mirrored />
      </div>
      <div className="page-bottom">
        <NextButton onClick={onContinue} href="/team" icon={<ArrowIcon strokeWidth={2.6} />}>Go!</NextButton>
      </div>
    </Page>
  );
}

export interface TeamMember {
  name: string;
  avatarId: string;
}

/** "You and Kiwi are a team!" Shared by the fixture route and the live room connection. */
export function TeamScreen({ self, teammate, status, action }: {
  /** Null until the live room has told us who this player is. */
  self: TeamMember | null;
  teammate: TeamMember | null;
  status?: ReactNode;
  action: ReactNode;
}) {
  return (
    <Page hills className="team-page">
      <Clouds />
      <div className="page-top">
        <MusicButton />
      </div>
      <h1 className="page-title team-title">{teammate ? `You and ${teammate.name} are a team!` : 'Your team'}</h1>
      <svg className="team-rainbow bob" viewBox="0 0 170 96" fill="none" strokeLinecap="round" aria-hidden="true">
        <path d="M14 88A71 71 0 0 1 156 88" stroke="#FF6F59" strokeWidth="12" />
        <path d="M30 88A55 55 0 0 1 140 88" stroke="#FFC83D" strokeWidth="12" />
        <path d="M46 88A39 39 0 0 1 124 88" stroke="#2EC4A0" strokeWidth="12" />
        <path d="M62 88A23 23 0 0 1 108 88" stroke="#6C4DF6" strokeWidth="12" />
      </svg>
      {self ? (
        <div className="team-pair">
          <div className="team-member">
            <Avatar id={self.avatarId} className="team-avatar" label={`${self.name}, you`} />
            <div className="name-pill">{self.name}</div>
          </div>
          {teammate ? (
            <div className="team-member">
              <Avatar id={teammate.avatarId} className="team-avatar" label={teammate.name} />
              <div className="name-pill">{teammate.name}</div>
            </div>
          ) : null}
        </div>
      ) : null}
      <div className="team-footer">
        <div className="team-status">{status}</div>
        <Drawy pose="cheer" className="team-drawy bob-fast" />
      </div>
      <div className="page-bottom">{action}</div>
    </Page>
  );
}

export function FixtureTeamScreen() {
  return (
    <TeamScreen
      self={{ name: 'Mango', avatarId: 'mango' }}
      teammate={{ name: 'Kiwi', avatarId: 'kiwi' }}
      action={<BigLink href="/play/speaker" icon={<ArrowIcon strokeWidth={2.6} />}>Let&apos;s play!</BigLink>}
    />
  );
}
