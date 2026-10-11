/** Minimal controllable WebSocket for room tests. Real sockets are exercised in the browser/API smoke checks. */
export class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  static readonly OPEN = 1;
  readyState = 0;
  sent: Array<Record<string, unknown>> = [];
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;

  constructor(public url: string) {
    FakeWebSocket.instances.push(this);
  }

  send(data: string) {
    this.sent.push(JSON.parse(data));
  }

  close() {
    this.readyState = 3;
  }

  /** Server accepted the connection. */
  open() {
    this.readyState = FakeWebSocket.OPEN;
    this.onopen?.();
  }

  receive(message: Record<string, unknown>) {
    this.onmessage?.({ data: JSON.stringify(message) });
  }

  drop() {
    this.readyState = 3;
    this.onclose?.();
  }

  static reset() {
    FakeWebSocket.instances = [];
  }

  static get latest(): FakeWebSocket {
    return FakeWebSocket.instances[FakeWebSocket.instances.length - 1];
  }
}

export function snapshotMessage(overrides: { phase?: string; role?: string; ready?: { self_ready: boolean; teammate_ready: boolean }; teammate?: string; teammateStatus?: string; version?: number } = {}) {
  const { phase = 'role_intro', role = 'drawer', ready, teammate = 'Kiwi', teammateStatus = 'connected', version = 1 } = overrides;
  return {
    protocol_version: 1,
    type: 'state.snapshot',
    payload: {
      snapshot_id: 'snap',
      session_player_id: 'player-1',
      room: {
        room_id: 'room-1',
        pair_id: 'pair-1',
        participant: { player_id: 'player-1', nickname: 'Mango', avatar_id: 'mango', connection_status: 'connected' },
        teammate: { player_id: 'player-2', nickname: teammate, avatar_id: 'kiwi', connection_status: teammateStatus },
      },
      round: { round_id: 'round-1', role, phase, phase_version: version, permissions: [] },
      drawing: { round_id: 'round-1', revision: 0, strokes: [] },
      ...(ready ? { ready } : {}),
    },
  };
}

export const waitingMessage = {
  protocol_version: 1,
  type: 'state.snapshot',
  payload: {
    session_player_id: 'player-1',
    admission_status: 'waiting_for_teammate',
    room: { room_id: 'room-1', participant: { player_id: 'player-1', nickname: 'Mango', avatar_id: 'mango', connection_status: 'connected' } },
  },
};
