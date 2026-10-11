import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MusicProvider } from '../../app/ui/frame';
import { FakeWebSocket, snapshotMessage, waitingMessage } from '../../test/fakeWebSocket';
import type { GuestSession } from '../rooms/api';
import { hasMicrophone } from '../voice/voice';
import { LiveGame } from './LiveGame';

vi.mock('../voice/voice', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../voice/voice')>()),
  hasMicrophone: vi.fn(() => true),
}));

const session: GuestSession = {
  room_id: 'room-1', player_id: 'player-1', guest_session_token: 'secret-token', expires_at: '2099-01-01T00:00:00Z',
};

function connect(onExit = vi.fn()) {
  render(<MusicProvider><LiveGame session={session} justJoined={false} onExit={onExit} /></MusicProvider>);
  const socket = FakeWebSocket.latest;
  act(() => socket.open());
  act(() => socket.receive({ protocol_version: 1, type: 'session.authenticated', payload: {} }));
  return socket;
}

beforeEach(() => {
  FakeWebSocket.reset();
  vi.stubGlobal('WebSocket', FakeWebSocket);
  vi.stubGlobal('crypto', { randomUUID: () => 'command-1' });
  URL.createObjectURL = vi.fn(() => 'blob:picture');
  URL.revokeObjectURL = vi.fn();
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  window.sessionStorage.clear();
});

describe('LiveGame', () => {
  it('asks for the mic again when a reloaded tab resumes its session, then goes straight back to the game', async () => {
    vi.mocked(hasMicrophone).mockReturnValueOnce(false);
    const user = userEvent.setup();
    const socket = connect();
    act(() => socket.receive(snapshotMessage({ role: 'speaker' })));
    expect(screen.getByRole('heading', { name: 'Can we hear you?' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Turn on mic' }));

    expect(await screen.findByRole('heading', { name: 'You and Kiwi are a team!' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Pick a game!' })).not.toBeInTheDocument();
  });

  it('authenticates first, then shows waiting and the paired team screen', () => {
    const socket = connect();
    expect(socket.url).toBe('ws://localhost:3000/api/v1/rooms/room-1/socket');
    expect(socket.sent[0]).toEqual({ protocol_version: 1, type: 'session.authenticate', payload: { guest_session_token: 'secret-token' } });

    act(() => socket.receive(waitingMessage));
    expect(screen.getByRole('status')).toHaveTextContent('Waiting for a teammate...');

    act(() => socket.receive(snapshotMessage({ role: 'speaker' })));
    expect(screen.getByRole('heading', { name: 'You and Kiwi are a team!' })).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('Round 1 of 3. You talk!');
  });

  it("sends one versioned Let's play acknowledgement and then waits for the teammate", async () => {
    const socket = connect();
    act(() => socket.receive(snapshotMessage({ version: 3 })));

    await userEvent.setup().click(screen.getByRole('button', { name: "Let's play!" }));
    expect(socket.sent[1]).toEqual({
      protocol_version: 1, type: 'round.intro.seen', command_id: 'command-1', round_id: 'round-1',
      payload: { expected_round_version: 3 },
    });

    act(() => socket.receive(snapshotMessage({ version: 3, ready: { self_ready: true, teammate_ready: false } })));
    expect(screen.getByRole('status')).toHaveTextContent('Waiting for Kiwi to be ready...');
    expect(screen.queryByRole('button', { name: "Let's play!" })).not.toBeInTheDocument();
  });

  it('streams the drawer strokes to the server and submits with Done', async () => {
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue(
      { left: 0, top: 0, width: 760, height: 680, right: 760, bottom: 680, x: 0, y: 0, toJSON: () => ({}) } as DOMRect,
    );
    const socket = connect();
    act(() => socket.receive(snapshotMessage({ phase: 'collaborating', role: 'drawer', version: 2 })));

    const area = screen.getByRole('img', { name: 'Drawing area' });
    fireEvent.pointerDown(area, { clientX: 76, clientY: 68, pointerId: 1 });
    fireEvent.pointerMove(area, { clientX: 380, clientY: 340, pointerId: 1 });
    fireEvent.pointerUp(area, { pointerId: 1 });
    const added = socket.sent.find((message) => message.type === 'drawing.add') as { round_id: string; payload: { stroke: { points: unknown[] } } };
    expect(added.round_id).toBe('round-1');
    expect(added.payload.stroke.points).toEqual([{ x: 0.1, y: 0.1 }, { x: 0.5, y: 0.5 }]);

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: 'Undo' }));
    expect(socket.sent.at(-1)).toMatchObject({ type: 'drawing.undo', round_id: 'round-1' });
    await user.click(screen.getByRole('button', { name: 'Done' }));
    expect(socket.sent.at(-1)).toMatchObject({ type: 'round.submit', round_id: 'round-1', payload: { expected_round_version: 2 } });
  });

  it('shows the speaker the authorized picture and the live drawing', async () => {
    const fetchMock = vi.fn(async () => new Response(new Blob(['<svg/>'], { type: 'image/svg+xml' })));
    vi.stubGlobal('fetch', fetchMock);
    const socket = connect();
    act(() => socket.receive(snapshotMessage({
      phase: 'collaborating', role: 'speaker',
      strokes: [{ stroke_id: 's1', color: '#E5483D', width: 14, points: [{ x: 0.1, y: 0.1 }, { x: 0.5, y: 0.5 }] }],
      extra: { object_access: { object_id: 'apple', display_name: 'Apple', image_url: '/api/v1/rounds/round-1/picture' } },
    })));

    expect(await screen.findByRole('img', { name: 'Apple' })).toHaveAttribute('src', 'blob:picture');
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/rounds/round-1/picture', { headers: { Authorization: 'Bearer secret-token' } });
    expect(document.querySelector('.partner-canvas path')).toHaveAttribute('d', 'M76 68 L380 340');
  });

  it('shows the neutral result with Play again, and Done leaves the room', async () => {
    const fetchMock = vi.fn(async () => new Response('{"status":"left"}'));
    vi.stubGlobal('fetch', fetchMock);
    const onExit = vi.fn();
    const socket = connect(onExit);
    act(() => socket.receive(snapshotMessage({
      phase: 'exploring', permissions: ['view_drawing', 'play_again'], ready: { self_ready: false, teammate_ready: true },
      extra: { feedback: { shared_result: { status: 'neutral_unscored', child_summary: 'x' }, role_feedback: { role: 'drawer', lines: ['Line one.', 'Line two.'] }, sticker_id: 'apple' } },
    })));
    expect(screen.getByRole('heading', { name: 'Great teamwork!' })).toBeInTheDocument();
    expect(screen.getByText('Kiwi wants to play again!')).toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: 'Play again' }));
    expect(socket.sent.at(-1)).toMatchObject({ type: 'round.play_again', round_id: 'round-1' });

    await user.click(screen.getByRole('button', { name: 'Done' }));
    await waitFor(() => expect(onExit).toHaveBeenCalled());
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/session/leave', expect.objectContaining({ method: 'POST' }));
  });

  it('hides Play again after the last round', () => {
    const socket = connect();
    act(() => socket.receive(snapshotMessage({ phase: 'exploring', roundIndex: 3, permissions: ['view_drawing'] })));

    expect(screen.queryByRole('button', { name: 'Play again' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Done' })).toBeInTheDocument();
  });

  it('tells the child when their teammate had to go', () => {
    const socket = connect();
    act(() => socket.receive({ ...waitingMessage, payload: { ...waitingMessage.payload, admission_status: 'teammate_left' } }));

    expect(screen.getByRole('status')).toHaveTextContent('Your teammate had to go.');
    expect(screen.getByRole('button', { name: 'Done' })).toBeInTheDocument();
  });

  it('reconnects with the same session after the connection drops, without replaying commands', () => {
    vi.useFakeTimers();
    const first = connect();
    act(() => first.receive(snapshotMessage()));

    act(() => first.drop());
    expect(screen.getByRole('status')).toHaveTextContent('Reconnecting...');
    act(() => { vi.advanceTimersByTime(1000); });

    expect(FakeWebSocket.instances).toHaveLength(2);
    act(() => FakeWebSocket.latest.open());
    expect(FakeWebSocket.latest.sent).toEqual([
      { protocol_version: 1, type: 'session.authenticate', payload: { guest_session_token: 'secret-token' } },
    ]);
  });

  it('ends cleanly when the server no longer accepts the session', () => {
    window.sessionStorage.setItem('heary_guest_session', 'stale');
    const onExit = vi.fn();
    const socket = connect(onExit);

    act(() => socket.receive({ protocol_version: 1, type: 'command.error', payload: { error: { code: 'session_invalid', message: 'Join again to continue.' } } }));

    expect(onExit).toHaveBeenCalled();
    expect(window.sessionStorage.getItem('heary_guest_session')).toBeNull();
    act(() => socket.drop());
    expect(FakeWebSocket.instances).toHaveLength(1);
  });
});
