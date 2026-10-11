// Line icons copied from the approved design files (24 x 24 grid, round caps).
// Each icon is sized by its context through the --icon custom property (see .icon in styles.css).
import type { CSSProperties, ReactNode } from 'react';

interface IconProps {
  strokeWidth?: number;
}

function Line({ strokeWidth = 2.4, children }: IconProps & { children: ReactNode }) {
  return (
    <svg
      className="icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

export function MusicIcon({ off = false, ...props }: IconProps & { off?: boolean }) {
  return (
    <Line {...props}>
      <path d="M9 18V5l11-2v13" />
      <circle cx="6" cy="18" r="3" />
      <circle cx="17" cy="16" r="3" />
      {off ? <path d="M3 3l18 18" /> : null}
    </Line>
  );
}

export function MicIcon(props: IconProps) {
  return (
    <Line {...props}>
      <path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3z" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18v3M8 21h8" />
    </Line>
  );
}

export function PencilIcon(props: IconProps) {
  return (
    <Line {...props}>
      <path d="M4 20l1-4L16.5 4.5a2.1 2.1 0 0 1 3 3L8 19l-4 1z" />
      <path d="M14 7l3 3" />
    </Line>
  );
}

export function ArrowIcon(props: IconProps) {
  return (
    <Line {...props}>
      <path d="M5 12h14M13 6l6 6-6 6" />
    </Line>
  );
}

export function CheckIcon(props: IconProps) {
  return (
    <Line {...props}>
      <path d="M5 12.5l4.5 4.5L19 7" />
    </Line>
  );
}

export function LockIcon(props: IconProps) {
  return (
    <Line {...props}>
      <rect x="5" y="11" width="14" height="9" rx="2" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
    </Line>
  );
}

export function KeyboardIcon(props: IconProps) {
  return (
    <Line {...props}>
      <rect x="2" y="6" width="20" height="12" rx="2" />
      <path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M7 14h10" />
    </Line>
  );
}

export function HourglassIcon(props: IconProps) {
  return (
    <Line {...props}>
      <path d="M6 3h12M6 21h12M7 3v4l5 5-5 5v4M17 3v4l-5 5 5 5v4" />
    </Line>
  );
}

export function CameraIcon(props: IconProps) {
  return (
    <Line {...props}>
      <path d="M4 8h3l2-3h6l2 3h3v11H4z" />
      <circle cx="12" cy="13" r="3.5" />
    </Line>
  );
}

export function SpinIcon(props: IconProps) {
  return (
    <Line {...props}>
      <path d="M4 12a8 8 0 0 1 13.5-5.8" />
      <path d="M18 2v5h-5" />
      <path d="M20 12a8 8 0 0 1-13.5 5.8" />
      <path d="M6 22v-5h5" />
    </Line>
  );
}

export function UndoIcon(props: IconProps) {
  return (
    <Line {...props}>
      <path d="M9 14L4 9l5-5" />
      <path d="M4 9h10a6 6 0 0 1 0 12h-3" />
    </Line>
  );
}

export function TrashIcon(props: IconProps) {
  return (
    <Line {...props}>
      <path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3" />
    </Line>
  );
}

export function SwapIcon(props: IconProps) {
  return (
    <Line {...props}>
      <path d="M4 8h14l-3-3M20 16H6l3 3" />
    </Line>
  );
}

export function HomeIcon(props: IconProps) {
  return (
    <Line {...props}>
      <path d="M4 11l8-7 8 7M6 10v10h12V10" />
    </Line>
  );
}

export function BackIcon(props: IconProps) {
  return (
    <Line {...props}>
      <path d="M15 6l-6 6 6 6" />
    </Line>
  );
}

const STAR_PATH = 'M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9L12 3z';

export function StarIcon({ filled, strokeWidth = 1.8, dashed = false, style }: {
  filled: boolean;
  strokeWidth?: number;
  dashed?: boolean;
  style?: CSSProperties;
}) {
  return (
    <svg
      className="icon"
      viewBox="0 0 24 24"
      fill={filled ? '#FFC83D' : '#fff'}
      stroke="#1B2B4B"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeDasharray={dashed ? '2 2.4' : undefined}
      aria-hidden="true"
      style={style}
    >
      <path d={STAR_PATH} />
    </svg>
  );
}
