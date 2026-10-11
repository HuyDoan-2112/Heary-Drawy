const SESSION_KEY = 'heary_guest_session';

// A separate, authorized admission flow is still a product decision. This client only resumes
// guest sessions already present on this device; it never discovers or joins a Room.
export interface GuestSession {
  room_id: string;
  player_id: string;
  guest_session_token: string;
  expires_at: string;
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

export function clearGuestSession(): void {
  window.sessionStorage.removeItem(SESSION_KEY);
}
