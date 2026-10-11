import { act, fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { FakeWebSocket } from '../test/fakeWebSocket';
import { App } from './App';
import { neutralResult } from './fixtures';
import { ResultScreen } from './screens/Finish';
import { MusicProvider } from './ui/frame';

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

function setViewport(width: number, height: number) {
  Object.defineProperty(window, 'innerWidth', { configurable: true, value: width });
  Object.defineProperty(window, 'innerHeight', { configurable: true, value: height });
}

beforeEach(() => {
  setViewport(820, 1180);
  FakeWebSocket.reset();
  vi.stubGlobal('WebSocket', FakeWebSocket);
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  window.sessionStorage.clear();
});

describe('approved screen flow', () => {
  it('starts on the character picker with Mango selected and a friend-picked Kiwi', async () => {
    const user = userEvent.setup();
    renderAt('/join');

    expect(screen.getByRole('heading', { name: 'Who are you?' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'I am Mango' })).toHaveAttribute('aria-pressed', 'true');
    const kiwi = screen.getByRole('button', { name: 'Kiwi, a friend already picked this' });
    expect(within(kiwi).getByText('Picked')).toBeInTheDocument();

    await user.click(kiwi);
    expect(screen.getByRole('button', { name: 'I am Mango' })).toHaveAttribute('aria-pressed', 'true');

    await user.click(screen.getByRole('button', { name: 'I am Plum' }));
    expect(screen.getByRole('button', { name: 'I am Plum' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('textbox', { name: 'My name, optional' })).toHaveAttribute('placeholder', 'My name (optional)');
  });

  it('resumes a stored guest session on the team screen without joining again', async () => {
    window.sessionStorage.setItem('heary_guest_session', JSON.stringify({
      room_id: 'room-test', player_id: 'player-test', guest_session_token: 'test-token', expires_at: '2099-01-01T00:00:00Z',
    }));
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    renderAt('/join');

    expect(await screen.findByText('Connecting to your room...')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Your team' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Who are you?' })).not.toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('walks from the character picker to the Speaker play screen without a full page load', async () => {
    const user = userEvent.setup();
    renderAt('/join');

    await user.click(screen.getByRole('link', { name: 'Go!' }));
    expect(screen.getByRole('heading', { name: 'Can we hear you?' })).toBeInTheDocument();

    await user.click(screen.getByRole('link', { name: 'Turn on mic' }));
    expect(screen.getByRole('heading', { name: 'Pick a game!' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Normal' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: /Advanced pictures are coming soon/ })).toHaveAttribute('aria-disabled', 'true');

    await user.click(screen.getByRole('link', { name: 'Go!' }));
    expect(screen.getByRole('heading', { name: 'You and Kiwi are a team!' })).toBeInTheDocument();

    await user.click(screen.getByRole('link', { name: "Let's play!" }));
    expect(screen.getByRole('heading', { name: 'You talk' })).toBeInTheDocument();
    expect(screen.getByText('You talk!')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'A red apple you can turn around. Drag it.' })).toBeInTheDocument();
  });

  it('keeps the Drawer play screen free of the secret picture before Reveal', () => {
    const { container } = renderAt('/play/drawer');

    expect(screen.getByRole('heading', { name: 'You draw' })).toBeInTheDocument();
    expect(screen.queryByRole('region', { name: 'Photo' })).not.toBeInTheDocument();
    expect(screen.queryByRole('img', { name: /apple/i })).not.toBeInTheDocument();
    expect(container).not.toHaveTextContent(/apple|object_id|image_url|model_url|rubric/i);
  });

  it('shows the Drawer canvas to the Speaker as a read-only live screen', () => {
    renderAt('/play/speaker');

    const live = screen.getByRole('img', { name: "Kiwi's screen, live" });
    expect(screen.queryByRole('img', { name: 'Drawing area' })).not.toBeInTheDocument();
    expect(within(live).queryByRole('button')).not.toBeInTheDocument();
  });

  it('lets the Drawer pick colors, undo, and clear only after confirming', async () => {
    const user = userEvent.setup();
    const { container } = renderAt('/play/drawer');
    const strokeCount = () => container.querySelectorAll('.drawing-strokes path').length;

    await user.click(screen.getByRole('button', { name: 'Blue' }));
    expect(screen.getByRole('button', { name: 'Blue' })).toHaveAttribute('aria-pressed', 'true');
    expect(strokeCount()).toBe(2);

    await user.click(screen.getByRole('button', { name: 'Undo' }));
    expect(strokeCount()).toBe(1);

    const confirm = vi.fn().mockReturnValueOnce(false).mockReturnValueOnce(true);
    vi.stubGlobal('confirm', confirm);
    await user.click(screen.getByRole('button', { name: 'Clear the drawing. Asks first' }));
    expect(strokeCount()).toBe(1);
    await user.click(screen.getByRole('button', { name: 'Clear the drawing. Asks first' }));
    expect(confirm).toHaveBeenCalledTimes(2);
    expect(strokeCount()).toBe(0);
  });

  it('uses the iPhone play layout on phones', () => {
    setViewport(390, 844);
    renderAt('/play/drawer');

    expect(screen.getByRole('img', { name: 'You draw' })).not.toHaveTextContent('You draw');
    expect(screen.getByRole('button', { name: 'Undo' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Clear the drawing. Asks first' })).not.toBeInTheDocument();
  });

  it('finishes through Drawy checking to the team result, and Play again swaps roles', async () => {
    const user = userEvent.setup();
    renderAt('/play/drawer');

    await user.click(screen.getByRole('link', { name: 'Done' }));
    expect(screen.getByRole('heading', { name: 'Drawy is looking' })).toBeInTheDocument();

    await user.click(screen.getByRole('link', { name: 'Demo: result is ready' }));
    expect(screen.getByRole('heading', { name: 'Great teamwork!' })).toBeInTheDocument();
    expect(screen.getByRole('img', { name: '2 of 3 stars' })).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'New sticker: apple' })).toBeInTheDocument();
    expect(screen.getByText('You got the red, round shape!')).toBeInTheDocument();
    expect(screen.getByText('Hmm... what else is at the top?')).toBeInTheDocument();

    await user.click(screen.getByRole('link', { name: 'Play again' }));
    expect(screen.getByRole('heading', { name: 'You draw' })).toBeInTheDocument();
  });

  it('shows a friendly neutral result without stars when scoring is unavailable', () => {
    render(<MusicProvider><ResultScreen result={neutralResult} /></MusicProvider>);

    expect(screen.getByRole('heading', { name: 'Great teamwork!' })).toBeInTheDocument();
    expect(screen.queryByRole('img', { name: /of 3 stars/ })).not.toBeInTheDocument();
    expect(screen.getByText(/Drawy had trouble checking this one/)).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'New sticker: apple' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Play again' })).toBeInTheDocument();
  });

  it('remembers the music choice across screens', async () => {
    const user = userEvent.setup();
    renderAt('/join');

    await user.click(screen.getByRole('button', { name: 'Music on or off' }));
    expect(screen.getByRole('button', { name: 'Music on or off' })).toHaveAttribute('aria-pressed', 'false');

    await user.click(screen.getByRole('link', { name: 'Go!' }));
    expect(screen.getByRole('button', { name: 'Music on or off' })).toHaveAttribute('aria-pressed', 'false');
  });

  it('opens the sample parent area only after a 3 second grown-up hold', async () => {
    const user = userEvent.setup();
    renderAt('/join');
    await user.click(screen.getByRole('link', { name: 'Grown-ups' }));
    expect(screen.getByRole('heading', { name: 'Grown-ups only' })).toBeInTheDocument();

    vi.useFakeTimers();
    const hold = screen.getByRole('button', { name: 'I am a grown-up. Open parent area' });
    fireEvent.pointerDown(hold);
    act(() => { vi.advanceTimersByTime(2000); });
    fireEvent.pointerUp(hold);
    act(() => { vi.advanceTimersByTime(2000); });
    expect(screen.getByRole('heading', { name: 'Grown-ups only' })).toBeInTheDocument();

    fireEvent.pointerDown(hold);
    act(() => { vi.advanceTimersByTime(3000); });
    expect(screen.getByRole('heading', { name: 'For parents' })).toBeInTheDocument();
    expect(screen.getByText('Sample data')).toBeInTheDocument();
  });
});
