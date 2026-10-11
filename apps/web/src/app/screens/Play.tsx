import { useState } from 'react';
import { fixtureDrawing, palette, type FixtureStroke } from '../fixtures';
import { DrawingSurface, SpinningApple, Strokes, TalkBars } from '../ui/art';
import { useIsPhone } from '../ui/device';
import { Avatar, Drawy, MusicButton, Page } from '../ui/frame';
import { CameraIcon, CheckIcon, HourglassIcon, MicIcon, PencilIcon, SpinIcon, TrashIcon, UndoIcon } from '../ui/icons';

type Role = 'talk' | 'draw';

// Fixture pair from the approved designs: Mango describes, Kiwi draws.
const SPEAKER = { name: 'Mango', avatarId: 'mango' };
const DRAWER = { name: 'Kiwi', avatarId: 'kiwi' };

function TopBar({ role }: { role: Role }) {
  const phone = useIsPhone();
  const self = role === 'talk' ? SPEAKER : DRAWER;
  const label = role === 'talk' ? 'You talk' : 'You draw';
  return (
    <header className="play-top">
      <MusicButton />
      <div className={`role-chip role-${role}`} role="img" aria-label={label}>
        <Avatar id={self.avatarId} className="chip-avatar" />
        {role === 'talk' ? <MicIcon strokeWidth={2.2} /> : <PencilIcon strokeWidth={2.2} />}
        {/* The iPhone design shows only the avatar and icon. */}
        {phone ? null : <span className="role-chip-text">{label}</span>}
      </div>
      {/* Fixture: round timing and time-up behavior are not decided yet. */}
      <div className="time-left" role="img" aria-label="Time left">
        <HourglassIcon strokeWidth={2.2} />
        <div className="time-track"><div className="time-fill" style={{ width: '38%' }} /></div>
      </div>
    </header>
  );
}

/** Short role intro that fades into the play screen after about 3 seconds. */
function RoleIntro({ role }: { role: Role }) {
  return (
    <div className={`role-intro role-${role}`}>
      <div className="intro-dots" role="img" aria-label="Round 1 of 3">
        <span data-current="true" />
        <span />
        <span />
      </div>
      <div className="intro-disc">
        {role === 'talk' ? <MicIcon strokeWidth={1.9} /> : <PencilIcon strokeWidth={1.9} />}
      </div>
      <div className="intro-title">{role === 'talk' ? 'You talk!' : 'You draw!'}</div>
      <Drawy pose={role === 'talk' ? 'talk' : 'proud'} className="intro-drawy bob-quick" mirrored />
    </div>
  );
}

function HoldToTalk({ partner, className }: { partner: string; className: string }) {
  return (
    <button type="button" className={`hold-button ${className}`} aria-label={`Hold to talk. ${partner} hears you right away`}>
      <MicIcon strokeWidth={2} />
      Hold to talk
    </button>
  );
}

export function SpeakerPlayScreen() {
  const phone = useIsPhone();

  return (
    <Page className="play-page speaker-page">
      <h1 className="sr-only">You talk</h1>
      <TopBar role="talk" />
      <section className="photo-card" aria-label="Photo">
        <div className="photo-chip">
          <CameraIcon strokeWidth={2.2} />
          Photo
        </div>
        <div className="spin-chip" aria-hidden="true">
          <SpinIcon />
          {phone ? 'Spin' : 'Spin it'}
        </div>
        <div className="photo-stage">
          <SpinningApple />
        </div>
      </section>
      <section className="partner-screen" role="img" aria-label={`${DRAWER.name}'s screen, live`}>
        <div className="partner-bar">
          <span className="live-dot" />
          <Avatar id={DRAWER.avatarId} className="partner-avatar" />
          <span className="partner-name">{DRAWER.name}</span>
          <span className="partner-talking" role="img" aria-label={`${DRAWER.name} is talking`}>
            <TalkBars count={5} className="bars-live" />
          </span>
        </div>
        <div className="partner-canvas">
          <Strokes strokes={fixtureDrawing} strokeWidth={14} className="fill-svg" />
        </div>
      </section>
      <HoldToTalk partner={DRAWER.name} className="hold-speaker" />
      <RoleIntro role="talk" />
    </Page>
  );
}

export function DrawerPlayScreen() {
  const phone = useIsPhone();
  const [color, setColor] = useState<string>(palette[0].color);
  const [strokes, setStrokes] = useState<FixtureStroke[]>(fixtureDrawing);

  return (
    <Page className="play-page drawer-page">
      <h1 className="sr-only">You draw</h1>
      <TopBar role="draw" />
      <div className="speaker-strip" role="img" aria-label={`${SPEAKER.name} is talking`}>
        <Avatar id={SPEAKER.avatarId} className="strip-avatar" />
        <TalkBars count={phone ? 7 : 11} className="bars-strip" />
      </div>
      <div className="drawing-card">
        <DrawingSurface strokes={strokes} color={color} onStroke={(stroke) => setStrokes([...strokes, stroke])} />
      </div>
      <div className="drawing-tools">
        {palette.map((swatch) => (
          <button
            key={swatch.color}
            type="button"
            className="swatch"
            style={{ background: swatch.color }}
            aria-label={swatch.label}
            aria-pressed={color === swatch.color}
            onClick={() => setColor(swatch.color)}
          />
        ))}
        <button type="button" className="tool-button tool-undo" aria-label="Undo" onClick={() => setStrokes(strokes.slice(0, -1))}>
          <UndoIcon strokeWidth={2.6} />
        </button>
        {/* Clear is iPad only in the approved design, and it always asks first. */}
        {phone ? null : (
          <button
            type="button"
            className="tool-button"
            aria-label="Clear the drawing. Asks first"
            onClick={() => {
              if (window.confirm('Clear your whole drawing?')) setStrokes([]);
            }}
          >
            <TrashIcon />
          </button>
        )}
      </div>
      <div className="drawer-actions">
        <HoldToTalk partner={SPEAKER.name} className="hold-drawer" />
        <a className="done-button" href="/checking" aria-label="Done">
          <CheckIcon strokeWidth={2.8} />
          Done!
        </a>
      </div>
      <RoleIntro role="draw" />
    </Page>
  );
}
