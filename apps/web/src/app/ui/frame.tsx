import type { ReactNode } from 'react';
import { createContext, useContext, useState } from 'react';
import { avatarAssets, drawyAssets, isAvatarId, type DrawyPose } from '../assets';
import { MusicIcon } from './icons';

/**
 * Full-screen page. Layout is fluid: sizes in styles.css interpolate between the approved iPhone
 * (390 px wide) and iPad (820 px wide) designs, so every screen fits the device it is on.
 */
export function Page({ tone = 'sky', hills = false, className, children }: {
  tone?: 'sky' | 'paper';
  hills?: boolean;
  className: string;
  children: ReactNode;
}) {
  return (
    <div className={`page tone-${tone}`}>
      {hills ? (
        <svg className="page-hills" viewBox="0 0 820 300" preserveAspectRatio="none" aria-hidden="true">
          <path d="M0 150 Q200 60 420 125 T820 100 V300 H0 Z" fill="#C6EED8" />
          <path d="M0 215 Q260 140 520 200 T820 175 V300 H0 Z" fill="#A6E0C0" />
        </svg>
      ) : null}
      <main className={`page-inner ${className}`}>{children}</main>
    </div>
  );
}

const CLOUD = 'M30 60 a24 24 0 0 1 8 -44 a30 30 0 0 1 56 -6 a26 26 0 0 1 44 24 a18 18 0 0 1 2 26 Z';

export function Clouds() {
  return (
    <>
      <svg className="cloud cloud-big" viewBox="0 0 170 70" aria-hidden="true"><path d={CLOUD} fill="#fff" opacity=".85" /></svg>
      <svg className="cloud cloud-small" viewBox="0 0 170 70" aria-hidden="true"><path d={CLOUD} fill="#fff" opacity=".7" /></svg>
    </>
  );
}

const MusicContext = createContext<{ on: boolean; toggle: () => void }>({ on: true, toggle: () => undefined });

export function MusicProvider({ children }: { children: ReactNode }) {
  const [on, setOn] = useState(true);
  return <MusicContext.Provider value={{ on, toggle: () => setOn((value) => !value) }}>{children}</MusicContext.Provider>;
}

/** Music on/off toggle. There is no soundtrack yet, so it only records the child's choice. */
export function MusicButton() {
  const { on, toggle } = useContext(MusicContext);
  return (
    <button type="button" className="music-button" aria-label="Music on or off" aria-pressed={on} onClick={toggle}>
      <MusicIcon off={!on} />
    </button>
  );
}

/** Inline design artwork. The caller's class sets the size. */
function Artwork({ svg, className, label, mirrored = false }: {
  svg: string;
  className: string;
  label?: string;
  mirrored?: boolean;
}) {
  return (
    <span
      className={`artwork ${className}`}
      style={mirrored ? { transform: 'scaleX(-1)' } : undefined}
      role={label ? 'img' : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      // Static, bundled design artwork only; never user or server content.
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}

export function Drawy({ pose, className, mirrored = false }: { pose: DrawyPose; className: string; mirrored?: boolean }) {
  return <Artwork svg={drawyAssets[pose]} className={className} label="Drawy" mirrored={mirrored} />;
}

export function Avatar({ id, className, label }: { id: string; className: string; label?: string }) {
  if (!isAvatarId(id)) return <span className={`artwork ${className}`} aria-hidden="true" />;
  return <Artwork svg={avatarAssets[id]} className={className} label={label} />;
}
