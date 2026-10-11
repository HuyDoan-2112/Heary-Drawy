import { useEffect, useRef } from 'react';
import { navigate } from '../router';
import { Avatar, Page } from '../ui/frame';
import { BackIcon, CheckIcon, LockIcon, StarIcon } from '../ui/icons';

const HOLD_MS = 3000;

/**
 * Grown-up gate from the approved design. A long press keeps young children out of the parent area;
 * it is not authorization. The parent area behind it shows sample data only.
 */
export function GrownupsGateScreen() {
  const timer = useRef<number | undefined>(undefined);

  const start = () => {
    if (timer.current !== undefined) return;
    timer.current = window.setTimeout(() => navigate('/grownups/parents'), HOLD_MS);
  };
  const cancel = () => {
    window.clearTimeout(timer.current);
    timer.current = undefined;
  };
  useEffect(() => cancel, []);

  return (
    <Page hills className="gate-page">
      <div className="page-top">
        <a className="gate-back" href="/join" aria-label="Back to the game">
          <BackIcon strokeWidth={2.6} />
        </a>
      </div>
      <div className="gate-intro">
        <div className="gate-lock"><LockIcon strokeWidth={1.9} /></div>
        <h1>Grown-ups only</h1>
        <p>This area has parent feedback and settings. Ask a grown-up to continue.</p>
      </div>
      <div className="gate-card">
        <div className="gate-card-title">Grown-up check</div>
        <div className="gate-card-copy">Press and hold the button for 3 seconds. Children should not open this part on their own.</div>
      </div>
      <div className="page-bottom">
        <button
          type="button"
          className="gate-hold"
          aria-label="I am a grown-up. Open parent area"
          onPointerDown={start}
          onPointerUp={cancel}
          onPointerLeave={cancel}
          onPointerCancel={cancel}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') start();
          }}
          onKeyUp={cancel}
          onContextMenu={(event) => event.preventDefault()}
        >
          <CheckIcon strokeWidth={2.6} />
          Hold to open
        </button>
      </div>
    </Page>
  );
}

function SmallStars({ filled }: { filled: number }) {
  return (
    <span className="parent-stars" role="img" aria-label={`${filled} of 3 stars`}>
      {[0, 1, 2].map((index) => <StarIcon key={index} filled={index < filled} />)}
    </span>
  );
}

const SAMPLE_SCORES = [
  { label: 'Details given', value: 60, color: '#FFC83D' },
  { label: 'Did not say the name', value: 100, color: '#2EC4A0' },
  { label: 'Partner asked', value: 50, color: '#FFC83D' },
  { label: 'Answers helped', value: 70, color: '#2EC4A0' },
  { label: 'Drawing matched', value: 67, color: '#FFC83D' },
];

export function ParentsScreen() {
  return (
    <Page tone="paper" className="parents-page">
      <header className="parents-header">
        <a className="parents-back" href="/join" aria-label="Back to the game">
          <BackIcon strokeWidth={2.6} />
        </a>
        <h1>For parents</h1>
        <span className="sample-badge">Sample data</span>
      </header>
      <section className="parents-card parents-summary">
        <Avatar id="mango" className="parents-avatar" label="Mango" />
        <div>
          <div className="parents-summary-title">Mango played today</div>
          <div className="parents-summary-meta">3 rounds · 12 minutes · 7 of 9 stars</div>
        </div>
      </section>
      <section className="parents-card parents-round">
        <div className="parents-round-head">
          <h2>Round 1 · Apple</h2>
          <SmallStars filled={2} />
        </div>
        <div className="parents-round-roles">Mango described · partner Kiwi drew</div>
        {SAMPLE_SCORES.map((score) => (
          <div className="score-row" key={score.label}>
            <span className="score-label">{score.label}</span>
            <div className="score-track"><div style={{ width: `${score.value}%`, background: score.color }} /></div>
            <span className="score-value">{score.value}%</span>
          </div>
        ))}
        <div className="parents-note">Mentioned color and shape. Did not mention the leaf on top.</div>
        <div className="parents-fineprint">Speech clarity is not scored. AI estimates can be wrong.</div>
      </section>
      <div className="parents-rounds">
        <div className="parents-round-row">Round 2 · Ball<SmallStars filled={3} /></div>
        <div className="parents-round-row">Round 3 · House<SmallStars filled={2} /></div>
      </div>
      <section className="parents-tip">
        <div className="parents-tip-title">Try at home</div>
        <div className="parents-tip-copy">Play &quot;guess my toy&quot;: describe a toy without saying its name, then swap.</div>
      </section>
      <p className="parents-footer">Voice is not saved as audio; it is turned into text for feedback. A practice game, not a test.</p>
    </Page>
  );
}
