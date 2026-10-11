import type { ReactNode } from 'react';
import { useState } from 'react';
import { fixtureDrawing, palette, type FixtureStroke } from '../fixtures';
import { DrawingSurface, SpinningApple, Strokes, TalkBars } from '../ui/art';
import type { DrawnStroke } from '../ui/drawing';
import { useIsPhone } from '../ui/device';
import { Avatar, Drawy, MusicButton, Page } from '../ui/frame';
import { CameraIcon, CheckIcon, HourglassIcon, MicIcon, PencilIcon, SpinIcon, TrashIcon, UndoIcon } from '../ui/icons';

type Role = 'talk' | 'draw';

// Fixture pair from the approved designs: Mango describes, Kiwi draws.
const SPEAKER = { name: 'Mango', avatarId: 'mango' };
const DRAWER = { name: 'Kiwi', avatarId: 'kiwi' };

export interface Teammate {
  name: string;
  avatarId: string;
}

export interface TalkControls {
  holding: boolean;
  start: () => void;
  stop: () => void;
}

const fixtureTalk: TalkControls = { holding: false, start: () => undefined, stop: () => undefined };

function TopBar({ role, selfAvatarId }: { role: Role; selfAvatarId: string }) {
  const phone = useIsPhone();
  const label = role === 'talk' ? 'You talk' : 'You draw';
  return (
    <header className="play-top">
      <MusicButton />
      <div className={`role-chip role-${role}`} role="img" aria-label={label}>
        <Avatar id={selfAvatarId} className="chip-avatar" />
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

function HoldToTalk({ partner, className, talk }: { partner: string; className: string; talk: TalkControls }) {
  return (
    <button
      type="button"
      className={`hold-button ${className}`}
      data-holding={talk.holding}
      aria-label={`Hold to talk. ${partner} hears you right away`}
      onPointerDown={(event) => {
        event.currentTarget.setPointerCapture?.(event.pointerId);
        talk.start();
      }}
      onPointerUp={talk.stop}
      onPointerCancel={talk.stop}
      onLostPointerCapture={() => {
        if (talk.holding) talk.stop();
      }}
      onContextMenu={(event) => event.preventDefault()}
    >
      <MicIcon strokeWidth={2} />
      Hold to talk
    </button>
  );
}

export interface SpeakerPlayProps {
  selfAvatarId: string;
  teammate: Teammate;
  picture: ReactNode;
  strokes: FixtureStroke[];
  teammateTalking: boolean;
  talk: TalkControls;
}

export function SpeakerPlayView({ selfAvatarId, teammate, picture, strokes, teammateTalking, talk }: SpeakerPlayProps) {
  const phone = useIsPhone();

  return (
    <Page className="play-page speaker-page">
      <h1 className="sr-only">You talk</h1>
      <TopBar role="talk" selfAvatarId={selfAvatarId} />
      <section className="photo-card" aria-label="Photo">
        <div className="photo-chip">
          <CameraIcon strokeWidth={2.2} />
          Photo
        </div>
        <div className="spin-chip" aria-hidden="true">
          <SpinIcon />
          {phone ? 'Spin' : 'Spin it'}
        </div>
        <div className="photo-stage">{picture}</div>
      </section>
      <section className="partner-screen" role="img" aria-label={`${teammate.name}'s screen, live`}>
        <div className="partner-bar">
          <span className="live-dot" />
          <Avatar id={teammate.avatarId} className="partner-avatar" />
          <span className="partner-name">{teammate.name}</span>
          {teammateTalking ? (
            <span className="partner-talking" role="img" aria-label={`${teammate.name} is talking`}>
              <TalkBars count={5} className="bars-live" />
            </span>
          ) : null}
        </div>
        <div className="partner-canvas">
          <Strokes strokes={strokes} strokeWidth={14} className="fill-svg" />
        </div>
      </section>
      <HoldToTalk partner={teammate.name} className="hold-speaker" talk={talk} />
      <RoleIntro role="talk" />
    </Page>
  );
}

export function SpeakerPlayScreen() {
  return (
    <SpeakerPlayView
      selfAvatarId={SPEAKER.avatarId}
      teammate={DRAWER}
      picture={<SpinningApple />}
      strokes={fixtureDrawing}
      teammateTalking
      talk={fixtureTalk}
    />
  );
}

export interface DrawerPlayProps {
  selfAvatarId: string;
  teammate: Teammate;
  strokes: FixtureStroke[];
  teammateTalking: boolean;
  talk: TalkControls;
  onStroke: (stroke: DrawnStroke) => void;
  onUndo: () => void;
  onClear: () => void;
  /** Live rounds submit the drawing; the fixture route links to the checking preview. */
  onDone?: () => void;
}

export function DrawerPlayView({ selfAvatarId, teammate, strokes, teammateTalking, talk, onStroke, onUndo, onClear, onDone }: DrawerPlayProps) {
  const phone = useIsPhone();
  const [color, setColor] = useState<string>(palette[0].color);
  const doneContent = (
    <>
      <CheckIcon strokeWidth={2.8} />
      Done!
    </>
  );

  return (
    <Page className="play-page drawer-page">
      <h1 className="sr-only">You draw</h1>
      <TopBar role="draw" selfAvatarId={selfAvatarId} />
      <div className="speaker-strip" role="img" aria-label={teammateTalking ? `${teammate.name} is talking` : teammate.name}>
        <Avatar id={teammate.avatarId} className="strip-avatar" />
        {teammateTalking ? <TalkBars count={phone ? 7 : 11} className="bars-strip" /> : null}
      </div>
      <div className="drawing-card">
        <DrawingSurface strokes={strokes} color={color} onStroke={onStroke} />
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
        <button type="button" className="tool-button tool-undo" aria-label="Undo" onClick={onUndo}>
          <UndoIcon strokeWidth={2.6} />
        </button>
        {/* Clear is iPad only in the approved design, and it always asks first. */}
        {phone ? null : (
          <button
            type="button"
            className="tool-button"
            aria-label="Clear the drawing. Asks first"
            onClick={() => {
              if (window.confirm('Clear your whole drawing?')) onClear();
            }}
          >
            <TrashIcon />
          </button>
        )}
      </div>
      <div className="drawer-actions">
        <HoldToTalk partner={teammate.name} className="hold-drawer" talk={talk} />
        {onDone ? (
          <button type="button" className="done-button" aria-label="Done" onClick={onDone}>{doneContent}</button>
        ) : (
          <a className="done-button" href="/checking" aria-label="Done">{doneContent}</a>
        )}
      </div>
      <RoleIntro role="draw" />
    </Page>
  );
}

export function DrawerPlayScreen() {
  const [strokes, setStrokes] = useState<FixtureStroke[]>(fixtureDrawing);
  return (
    <DrawerPlayView
      selfAvatarId={DRAWER.avatarId}
      teammate={SPEAKER}
      strokes={strokes}
      teammateTalking
      talk={fixtureTalk}
      onStroke={(stroke) => setStrokes([...strokes, stroke])}
      onUndo={() => setStrokes(strokes.slice(0, -1))}
      onClear={() => setStrokes([])}
    />
  );
}
