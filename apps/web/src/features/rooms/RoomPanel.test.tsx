import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { FakeWebSocket, snapshotMessage, waitingMessage } from '../../test/fakeWebSocket';
import type { GuestSession } from './api';
import { RoomPanel } from './RoomPanel';

const session: GuestSession = {
  room_id: 'room-1', player_id: 'player-1', guest_session_token: 'secret-token', expires_at: '2099-01-01T00:00:00Z',
};

function connect() {
  render(<RoomPanel session={session} />);
  const socket = FakeWebSocket.latest;
  act(() => socket.open());
  return socket;
}

beforeEach(() => {
  FakeWebSocket.reset();
  vi.stubGlobal('WebSocket', FakeWebSocket);
  vi.stubGlobal('crypto', { randomUUID: () => 'command-1' });
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  window.sessionStorage.clear();
});

describe('RoomPanel', () => {
  it('authenticates first, then shows the waiting and paired states pushed by the server', () => {
    const socket = connect();
    expect(socket.url).toBe('ws://localhost:3000/api/v1/rooms/room-1/socket');
    expect(socket.sent).toEqual([{ protocol_version: 1, type: 'session.authenticate', payload: { guest_session_token: 'secret-token' } }]);
    expect(screen.getByRole('status')).toHaveTextContent('Connecting to your room...');

    act(() => socket.receive(waitingMessage));
    expect(screen.getByRole('status')).toHaveTextContent('Waiting for a teammate...');

    act(() => socket.receive(snapshotMessage({ role: 'speaker' })));
    expect(screen.getByRole('status')).toHaveTextContent('You are the Speaker. Teammate: Kiwi.');
  });

  it('sends one versioned role-intro acknowledgement and then waits for the teammate', async () => {
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

  it('shows presence and a friendly Play again flow', async () => {
    const socket = connect();
    act(() => socket.receive(snapshotMessage({ phase: 'exploring', teammateStatus: 'disconnected', ready: { self_ready: false, teammate_ready: true } })));
    expect(screen.getByRole('status')).toHaveTextContent('Kiwi wants to play again!');

    await userEvent.setup().click(screen.getByRole('button', { name: 'Play again' }));
    expect(socket.sent[1]).toMatchObject({ type: 'round.play_again', round_id: 'round-1' });
  });

  it('reconnects with the same session after the connection drops, without replaying commands', () => {
    vi.useFakeTimers();
    const first = connect();
    act(() => first.receive(snapshotMessage()));

    act(() => first.drop());
    expect(screen.getByRole('status')).toHaveTextContent('Reconnecting...');
    expect(screen.queryByRole('button', { name: "Let's play!" })).not.toBeInTheDocument();
    act(() => { vi.advanceTimersByTime(1000); });

    expect(FakeWebSocket.instances).toHaveLength(2);
    act(() => FakeWebSocket.latest.open());
    expect(FakeWebSocket.latest.sent).toEqual([
      { protocol_version: 1, type: 'session.authenticate', payload: { guest_session_token: 'secret-token' } },
    ]);
  });

  it('ends the session cleanly when the server no longer accepts it', () => {
    window.sessionStorage.setItem('heary_guest_session', 'stale');
    const socket = connect();

    act(() => socket.receive({ protocol_version: 1, type: 'command.error', payload: { error: { code: 'session_invalid', message: 'Join again to continue.' } } }));

    expect(screen.getByRole('status')).toHaveTextContent('Your room session ended.');
    expect(screen.getByRole('alert')).toHaveTextContent('Join again');
    expect(window.sessionStorage.getItem('heary_guest_session')).toBeNull();
    act(() => socket.drop());
    expect(FakeWebSocket.instances).toHaveLength(1);
  });
});
