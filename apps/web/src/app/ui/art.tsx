import type { PointerEvent } from 'react';
import { useRef, useState } from 'react';
import type { FixtureStroke } from '../fixtures';
import { DRAWING_HEIGHT, DRAWING_WIDTH, toPath, type DrawnStroke, type Point } from './drawing';

const APPLE_BODY = 'M100 56C78 38 36 48 32 98c-4 52 32 90 54 86 8-2 10-5 14-5s6 3 14 5c22 4 58-34 54-86-4-50-46-60-68-42z';
const APPLE_LEAF = 'M104 40c12-18 36-20 50-10-6 16-30 26-50 10z';

// Half-width of the apple body at height y, and the freckles that slide around as it turns.
const APPLE_OUTLINE: [number, number][] = [[56, 0], [75, 45], [98, 68], [130, 64], [160, 50], [180, 28], [186, 0]];
const APPLE_SPOTS: [number, number][] = [[0, 85], [50, 120], [105, 100], [160, 140], [215, 90], [265, 125], [315, 105], [25, 150], [190, 155], [245, 70], [340, 70]];

function halfWidth(y: number): number {
  for (let i = 1; i < APPLE_OUTLINE.length; i++) {
    const [y1, w1] = APPLE_OUTLINE[i];
    if (y <= y1) {
      const [y0, w0] = APPLE_OUTLINE[i - 1];
      return w0 + ((w1 - w0) * (y - y0)) / (y1 - y0);
    }
  }
  return 0;
}

const toRadians = (degrees: number) => (degrees * Math.PI) / 180;

/**
 * Fixture stand-in for the Speaker's 3D reference, ported from the approved design: drag sideways
 * to turn the apple. Feature 04 replaces it with the authorized 3D object viewer.
 */
export function SpinningApple() {
  const [turn, setTurn] = useState(30);
  const dragX = useRef<number | null>(null);

  const onPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    event.currentTarget.setPointerCapture?.(event.pointerId);
    dragX.current = event.clientX;
  };
  const onPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    if (dragX.current === null) return;
    const delta = event.clientX - dragX.current;
    dragX.current = event.clientX;
    setTurn((value) => value + delta * 0.9);
  };
  const stopDrag = () => {
    dragX.current = null;
  };

  const leafAngle = toRadians(turn + 70);

  return (
    <div
      className="spinning-apple"
      role="img"
      aria-label="A red apple you can turn around. Drag it."
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={stopDrag}
      onPointerLeave={stopDrag}
      onPointerCancel={stopDrag}
    >
      <div className="apple-shadow" />
      <svg viewBox="0 0 200 200" aria-hidden="true">
        <path d={APPLE_BODY} fill="#E5483D" stroke="#1B2B4B" strokeWidth="5" strokeLinejoin="round" />
        {APPLE_SPOTS.map(([azimuth, y]) => {
          const angle = toRadians(azimuth + turn);
          const facing = Math.cos(angle);
          return (
            <ellipse
              key={`${azimuth}-${y}`}
              cx={100 + halfWidth(y) * 0.86 * Math.sin(angle)}
              cy={y}
              rx={5 * Math.max(0.2, facing)}
              ry={8}
              fill="#A82D26"
              opacity={facing > 0.1 ? Math.min(1, facing * 1.8) * 0.95 : 0}
            />
          );
        })}
        <rect x="95.5" y="22" width="9" height="40" rx="4.5" fill="#8B5A2B" />
        <path
          transform={`translate(104 0) scale(${Math.sin(leafAngle).toFixed(3)} 1) translate(-104 0)`}
          d={APPLE_LEAF}
          fill={Math.cos(leafAngle) >= 0 ? '#35B26B' : '#2A9158'}
          stroke="#1B2B4B"
          strokeWidth="4"
          strokeLinejoin="round"
        />
        <path d="M56 90c2-14 10-22 20-26" fill="none" stroke="#fff" strokeWidth="7" strokeLinecap="round" opacity=".5" />
      </svg>
    </div>
  );
}

/** The apple sticker earned on the result screen. */
export function AppleSticker() {
  return (
    <svg className="sticker-apple" viewBox="0 0 200 200" aria-hidden="true">
      <path d={APPLE_BODY} fill="#E5483D" stroke="#1B2B4B" strokeWidth="10" strokeLinejoin="round" />
      <path d={APPLE_LEAF} fill="#35B26B" stroke="#1B2B4B" strokeWidth="8" strokeLinejoin="round" />
    </svg>
  );
}

/** Read-only rendering of a drawing in the 760 x 680 design space. */
export function Strokes({ strokes, strokeWidth, className, label }: {
  strokes: FixtureStroke[];
  strokeWidth: number;
  className?: string;
  label?: string;
}) {
  return (
    <svg
      className={className}
      viewBox="0 0 760 680"
      preserveAspectRatio="xMidYMid meet"
      role={label ? 'img' : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    >
      {strokes.map((stroke, index) => (
        <path key={index} d={stroke.d} fill="none" stroke={stroke.color} strokeWidth={strokeWidth} strokeLinecap="round" />
      ))}
    </svg>
  );
}

/**
 * Finger drawing surface from the approved design. The 760 x 680 drawing is centered in the
 * canvas without stretching, and the child can keep drawing in any extra room around it.
 */
export function DrawingSurface({ strokes, color, onStroke }: {
  strokes: FixtureStroke[];
  color: string;
  onStroke: (stroke: DrawnStroke) => void;
}) {
  const [live, setLive] = useState<Point[] | null>(null);

  // Same fit as the SVG below (xMidYMid meet), inverted, so strokes land under the finger.
  const pointFrom = (event: PointerEvent<HTMLDivElement>): Point => {
    const rect = event.currentTarget.getBoundingClientRect();
    const scale = Math.min(rect.width / DRAWING_WIDTH, rect.height / DRAWING_HEIGHT);
    const offsetX = (rect.width - DRAWING_WIDTH * scale) / 2;
    const offsetY = (rect.height - DRAWING_HEIGHT * scale) / 2;
    return [
      Math.round((event.clientX - rect.left - offsetX) / scale),
      Math.round((event.clientY - rect.top - offsetY) / scale),
    ];
  };

  const finish = () => {
    if (live) onStroke({ d: toPath(live), color, points: live });
    setLive(null);
  };

  const shown = live ? [...strokes, { d: toPath(live), color }] : strokes;

  return (
    <>
      <svg className="drawing-strokes" viewBox={`0 0 ${DRAWING_WIDTH} ${DRAWING_HEIGHT}`} aria-hidden="true">
        {shown.map((stroke, index) => (
          <path key={index} d={stroke.d} fill="none" stroke={stroke.color} strokeWidth={14} strokeLinecap="round" strokeLinejoin="round" />
        ))}
      </svg>
      <div
        className="drawing-input"
        role="img"
        aria-label="Drawing area"
        onPointerDown={(event) => {
          event.currentTarget.setPointerCapture?.(event.pointerId);
          setLive([pointFrom(event)]);
        }}
        onPointerMove={(event) => {
          if (!live) return;
          const point = pointFrom(event);
          setLive((points) => (points ? [...points, point] : points));
        }}
        onPointerUp={finish}
        onPointerLeave={finish}
        onPointerCancel={finish}
      />
    </>
  );
}

/** Animated talking bars, as drawn in the play screen designs. */
export function TalkBars({ count, className }: { count: number; className: string }) {
  return (
    <span className={`talk-bars ${className}`} aria-hidden="true">
      {Array.from({ length: count }, (_, index) => (
        <span key={index} style={{ animationDelay: `${index / 10}s` }} />
      ))}
    </span>
  );
}
