import type { JoinRoomRequest, JoinRoomResponse, PendingRoomSnapshot, RoleFilteredSnapshot } from '../../generated/contracts';

const SESSION_KEY = 'heary_guest_session';

type GuestSession = Pick<JoinRoomResponse, 'room_id' | 'player_id' | 'guest_session_token' | 'expires_at'>;

export async function joinRoom(request: JoinRoomRequest): Promise<{ session?: GuestSession; error?: string }> {
  try {
    const response = await fetch('/api/v1/rooms/join', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const body: { error?: { code?: string } } = await response.json();
      return { error: body.error?.code === 'nickname_taken'
        ? 'That name is already taken here. Try another one!'
        : 'That room is not ready. Check the shapes with a grown-up.' };
    }
    const joined: JoinRoomResponse = await response.json();
    const session: GuestSession = {
      room_id: joined.room_id,
      player_id: joined.player_id,
      guest_session_token: joined.guest_session_token,
      expires_at: joined.expires_at,
    };
    window.sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
    return { session };
  } catch {
    return { error: 'Cannot reach the room right now. Ask a grown-up to try again.' };
  }
}

export function readGuestSession(): GuestSession | null {
  const raw = window.sessionStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    const parsed: GuestSession = JSON.parse(raw);
    if (typeof parsed.room_id !== 'string' || typeof parsed.player_id !== 'string' ||
        typeof parsed.guest_session_token !== 'string' || typeof parsed.expires_at !== 'string' ||
        !Number.isFinite(Date.parse(parsed.expires_at)) || Date.parse(parsed.expires_at) <= Date.now()) {
      window.sessionStorage.removeItem(SESSION_KEY);
      return null;
    }
    return parsed;
  } catch {
    window.sessionStorage.removeItem(SESSION_KEY);
    return null;
  }
}

export async function getRoomState(session: GuestSession): Promise<PendingRoomSnapshot | RoleFilteredSnapshot | null> {
  try {
    const response = await fetch(`/api/v1/rooms/${encodeURIComponent(session.room_id)}/state`, {
      headers: { Authorization: `Bearer ${session.guest_session_token}` },
    });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}
