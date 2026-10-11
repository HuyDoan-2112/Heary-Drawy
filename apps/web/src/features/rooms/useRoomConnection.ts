import { useCallback, useEffect, useRef, useState } from 'react';
import type { PendingRoomSnapshot, RoleFilteredSnapshot } from '../../generated/contracts';
import { clearGuestSession, type GuestSession } from './api';

export type RoomSnapshot = PendingRoomSnapshot | RoleFilteredSnapshot;
export type ConnectionState = 'connecting' | 'live' | 'reconnecting' | 'ended';
export type RoundCommand = 'round.intro.seen' | 'round.play_again';

const MAX_BACKOFF_MS = 8000;

interface ServerMessage {
  type: string;
  payload?: { error?: { code?: string; message?: string }; [key: string]: unknown };
}

/**
 * Keeps one authenticated socket open for the session. The server pushes a fresh role-filtered
 * snapshot after every change, so the UI renders whatever the latest snapshot says and never
 * guesses state locally. Reconnects use the same guest session and never replay commands.
 */
export function useRoomConnection(session: GuestSession | null) {
  const [snapshot, setSnapshot] = useState<RoomSnapshot | null>(null);
  const [connection, setConnection] = useState<ConnectionState>('connecting');
  const [notice, setNotice] = useState('');
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!session) return undefined;
    let stopped = false;
    let attempt = 0;
    let timer: number | undefined;

    const open = () => {
      setConnection(attempt === 0 ? 'connecting' : 'reconnecting');
      const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const socket = new WebSocket(`${scheme}://${window.location.host}/api/v1/rooms/${encodeURIComponent(session.room_id)}/socket`);
      socketRef.current = socket;
      socket.onopen = () => {
        socket.send(JSON.stringify({
          protocol_version: 1,
          type: 'session.authenticate',
          payload: { guest_session_token: session.guest_session_token },
        }));
      };
      socket.onmessage = (event: MessageEvent<string>) => {
        const message: ServerMessage = JSON.parse(event.data);
        if (message.type === 'state.snapshot') {
          attempt = 0;
          setConnection('live');
          setSnapshot(message.payload as unknown as RoomSnapshot);
        } else if (message.type === 'command.error') {
          const code = message.payload?.error?.code;
          if (code === 'session_invalid' || code === 'not_authorized') {
            stopped = true;
            clearGuestSession();
            setConnection('ended');
            setNotice('This room session ended. Join again to keep playing.');
            socket.close();
          } else {
            setNotice(message.payload?.error?.message ?? 'That did not work. Try again.');
            socket.send(JSON.stringify({ protocol_version: 1, type: 'state.request', payload: {} }));
          }
        }
      };
      socket.onclose = () => {
        if (stopped) return;
        attempt += 1;
        setConnection('reconnecting');
        timer = window.setTimeout(open, Math.min(1000 * 2 ** (attempt - 1), MAX_BACKOFF_MS));
      };
    };

    open();
    return () => {
      stopped = true;
      window.clearTimeout(timer);
      socketRef.current?.close();
    };
  }, [session]);

  const sendRoundCommand = useCallback((type: RoundCommand) => {
    const socket = socketRef.current;
    if (!snapshot || !('round' in snapshot) || socket?.readyState !== WebSocket.OPEN) return;
    setNotice('');
    socket.send(JSON.stringify({
      protocol_version: 1,
      type,
      command_id: crypto.randomUUID(),
      round_id: snapshot.round.round_id,
      payload: { expected_round_version: snapshot.round.phase_version },
    }));
  }, [snapshot]);

  return { snapshot, connection, notice, sendRoundCommand };
}
