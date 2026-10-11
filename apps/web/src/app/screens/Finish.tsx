import { fixtureDrawing, type ResultFixture } from '../fixtures';
import { AppleSticker, SpinningApple, Strokes } from '../ui/art';
import { Clouds, Drawy, MusicButton, Page } from '../ui/frame';
import { HomeIcon, StarIcon, SwapIcon } from '../ui/icons';

export function CheckingScreen() {
  return (
    <Page hills className="checking-page">
      <Clouds />
      <div className="page-top">
        <MusicButton />
      </div>
      <div className="checking-heading">
        <h1 className="page-title">Drawy is looking</h1>
        <span className="waiting-dots" role="img" aria-label="Please wait">
          <span />
          <span />
          <span />
        </span>
      </div>
      <div className="checking-scene">
        <div className="checking-drawing">
          <Strokes strokes={fixtureDrawing} strokeWidth={16} className="fill-svg" label="Your drawing" />
        </div>
        <Drawy pose="search" className="checking-drawy bob" mirrored />
      </div>
      <div className="page-bottom">
        {/* Fixture shortcut shown in the approved design until real finalizing state exists. */}
        <a className="demo-pill" href="/result">Demo: result is ready</a>
      </div>
    </Page>
  );
}

// Positions are percentages of the confetti band from the approved 820 px design.
const CONFETTI = [
  { left: 7.3, top: 58, round: true, size: 16, color: '#FFC83D', rotate: 0, duration: 2.2 },
  { left: 17.1, top: 83, round: false, size: 22, color: '#6C4DF6', rotate: 30, duration: 2.6 },
  { left: 84.1, top: 56, round: true, size: 18, color: '#2EC4A0', rotate: 0, duration: 2.0 },
  { left: 90.5, top: 83, round: false, size: 24, color: '#FF6F59', rotate: -25, duration: 2.4 },
  { left: 13.4, top: 33, round: true, size: 12, color: '#FF6F59', rotate: 0, duration: 2.8 },
  { left: 85.4, top: 33, round: true, size: 14, color: '#6C4DF6', rotate: 0, duration: 2.3 },
  { left: 4.9, top: 92, round: false, size: 20, color: '#2EC4A0', rotate: 60, duration: 2.1 },
  { left: 93.9, top: 69, round: true, size: 12, color: '#FFC83D', rotate: 0, duration: 2.7 },
];

function Stars({ count }: { count: 1 | 2 | 3 }) {
  return (
    <div className="result-stars" role="img" aria-label={`${count} of 3 stars`}>
      {[0, 1, 2].map((index) => (
        <StarIcon
          key={index}
          filled={index < count}
          dashed={index >= count}
          strokeWidth={1.5}
          style={{ animation: `popin .6s ease-out ${index * 0.25}s both` }}
        />
      ))}
    </div>
  );
}

/** Shared team result: 1-3 stars when scoring worked, a friendly neutral result when it did not. */
export function ResultScreen({ result }: { result: ResultFixture }) {
  return (
    <Page hills className="result-page">
      <Clouds />
      <div className="confetti-band" aria-hidden="true">
        {CONFETTI.map((piece, index) => (
          <span
            key={index}
            className="confetti"
            data-round={piece.round}
            style={{
              left: `${piece.left}%`,
              top: `${piece.top}%`,
              ['--confetti' as string]: piece.size,
              background: piece.color,
              rotate: `${piece.rotate}deg`,
              animationDuration: `${piece.duration}s`,
            }}
          />
        ))}
      </div>
      <div className="page-top">
        <MusicButton />
      </div>
      <h1 className="page-title result-title">Great teamwork!</h1>
      {result.stars ? <Stars count={result.stars} /> : null}
      <div className="result-cards">
        <div className="result-card">
          <div className="sticker" role="img" aria-label="New sticker: apple">
            <AppleSticker />
            <svg className="sticker-sparkle" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 2l2 7 7 3-7 3-2 7-2-7-7-3 7-3z" fill="#FFC83D" stroke="#1B2B4B" strokeWidth="1.6" strokeLinejoin="round" />
            </svg>
          </div>
          <div className="result-art">
            <SpinningApple />
          </div>
          <div className="result-card-label">Photo</div>
        </div>
        <div className="result-card">
          <div className="result-art">
            <Strokes strokes={fixtureDrawing} strokeWidth={16} className="fill-svg" label="Kiwi's drawing: a red circle with a brown stem" />
          </div>
          <div className="result-card-label">Kiwi&apos;s drawing</div>
        </div>
      </div>
      <div className="result-feedback">
        <Drawy pose="cheer" className="result-drawy bob" />
        <div className="speech-bubble" data-neutral={result.stars === null}>
          <span className="speech-tail" aria-hidden="true" />
          <div className="speech-praise">{result.praise}</div>
          <div className="speech-question">{result.question}</div>
        </div>
      </div>
      <div className="page-bottom result-actions">
        <a className="big-button result-again" href="/play/drawer">
          <SwapIcon strokeWidth={2.6} />
          Play again
        </a>
        <a className="big-button result-done" href="/join">
          <HomeIcon />
          Done
        </a>
      </div>
    </Page>
  );
}
