// "Happy Clappy Loop" by OwlishMedia, CC0: https://opengameart.org/content/happy-clappy-loop
import loopUrl from '../assets/happy-clappy-loop.m4a';

const VOLUME = 0.25;
const FADE_SECONDS = 0.4;

/**
 * Background music through Web Audio rather than <audio>: the loop is gapless, the level can be
 * set (iOS ignores <audio>.volume), and the iPhone silent switch mutes it like other app sounds.
 * Browsers only start sound from a tap, so the engine is created and resumed inside one.
 */
let context: AudioContext | null = null;
let gain: GainNode | null = null;
let wanted = false;
let listening = false;

function createEngine(): AudioContext {
  const audio = new AudioContext();
  const output = audio.createGain();
  output.gain.value = 0;
  output.connect(audio.destination);
  context = audio;
  gain = output;
  void fetch(loopUrl)
    .then((response) => response.arrayBuffer())
    .then((data) => audio.decodeAudioData(data))
    .then((buffer) => {
      const source = audio.createBufferSource();
      source.buffer = buffer;
      source.loop = true;
      source.connect(output);
      source.start();
    })
    // Music is decoration; the game works the same without it.
    .catch(() => undefined);
  return audio;
}

function fadeTo(level: number) {
  if (!context || !gain) return;
  const now = context.currentTime;
  gain.gain.cancelScheduledValues(now);
  gain.gain.setValueAtTime(gain.gain.value, now);
  gain.gain.linearRampToValueAtTime(level, now + FADE_SECONDS);
}

/** Starts or resumes the music. Must run inside a tap to be allowed to make sound. */
export function unlockMusic() {
  if (!wanted || typeof AudioContext === 'undefined') return;
  const audio = context ?? createEngine();
  if (audio.state !== 'running') void audio.resume().catch(() => undefined);
  fadeTo(VOLUME);
}

function listenForTaps() {
  if (listening) return;
  listening = true;
  // touchend/pointerup rather than *down: iOS only grants audio playback on the end of a tap.
  for (const type of ['pointerup', 'touchend', 'keydown'] as const) {
    document.addEventListener(type, unlockMusic, { capture: true });
  }
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) void context?.suspend().catch(() => undefined);
    else if (wanted) void context?.resume().catch(() => undefined);
  });
}

/** Fades the music in or out. Before the first tap it only records the wish. */
export function setMusicPlaying(playing: boolean) {
  if (typeof AudioContext === 'undefined') return;
  wanted = playing;
  listenForTaps();
  if (!context) return;
  if (playing) {
    void context.resume().catch(() => undefined);
    fadeTo(VOLUME);
  } else {
    fadeTo(0);
    window.setTimeout(() => {
      if (!wanted) void context?.suspend().catch(() => undefined);
    }, FADE_SECONDS * 1000 + 50);
  }
}
