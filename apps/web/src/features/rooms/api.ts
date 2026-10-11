import type { DeviceEnrollmentResponse, GuestAdmissionResponse } from '../../generated/contracts';

const SESSION_KEY = 'heary_guest_session';
const DEVICE_KEY = 'heary_device_enrollment';

// Both credentials live in sessionStorage so each browser tab acts as its own device.
export type GuestSession = Omit<GuestAdmissionResponse, 'admission_status'>;
export type DeviceEnrollment = DeviceEnrollmentResponse;

function readStored<T extends { room_id: string; expires_at: string }>(key: string, fields: (keyof T)[]): T | null {
  const raw = window.sessionStorage.getItem(key);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as T;
    const valid = fields.every((field) => typeof parsed[field] === 'string') &&
      Number.isFinite(Date.parse(parsed.expires_at)) && Date.parse(parsed.expires_at) > Date.now();
    if (valid) return parsed;
  } catch {
    // Fall through and drop the unreadable value.
  }
  window.sessionStorage.removeItem(key);
  return null;
}

export function readGuestSession(): GuestSession | null {
  return readStored<GuestSession>(SESSION_KEY, ['room_id', 'player_id', 'guest_session_token', 'expires_at']);
}

export function clearGuestSession(): void {
  window.sessionStorage.removeItem(SESSION_KEY);
}

export function readDeviceEnrollment(): DeviceEnrollment | null {
  return readStored<DeviceEnrollment>(DEVICE_KEY, ['room_id', 'device_token', 'expires_at']);
}

export function clearDeviceEnrollment(): void {
  window.sessionStorage.removeItem(DEVICE_KEY);
}

export class ApiError extends Error {
  constructor(readonly code: string, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit & { token?: string } = {}): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (init.token) headers.Authorization = `Bearer ${init.token}`;
  let response: Response;
  try {
    response = await fetch(path, { ...init, headers });
  } catch {
    throw new ApiError('network', 'Cannot reach the game right now. Try again in a moment.');
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(body?.error?.code ?? 'unknown', body?.error?.message ?? 'That did not work. Try again.');
  }
  return body as T;
}

/** A grown-up unlocks this device for a Room with the Room passcode. */
export async function enrollDevice(passcode: string): Promise<DeviceEnrollment> {
  const enrollment = await request<DeviceEnrollment>('/api/v1/device-enrollments', {
    method: 'POST',
    body: JSON.stringify({ passcode }),
  });
  window.sessionStorage.setItem(DEVICE_KEY, JSON.stringify(enrollment));
  return enrollment;
}

export async function fetchTakenAvatars(device: DeviceEnrollment): Promise<string[]> {
  const lobby = await request<{ taken_avatar_ids: string[] }>(`/api/v1/rooms/${encodeURIComponent(device.room_id)}/lobby`, {
    token: device.device_token,
  });
  return lobby.taken_avatar_ids;
}

export async function admitGuest(device: DeviceEnrollment, nickname: string, avatarId: string): Promise<GuestSession> {
  const admitted = await request<GuestAdmissionResponse>(`/api/v1/rooms/${encodeURIComponent(device.room_id)}/guests`, {
    method: 'POST',
    token: device.device_token,
    body: JSON.stringify({ nickname, avatar_id: avatarId }),
  });
  const session: GuestSession = {
    room_id: admitted.room_id,
    player_id: admitted.player_id,
    guest_session_token: admitted.guest_session_token,
    expires_at: admitted.expires_at,
  };
  window.sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
  return session;
}

/** Done: end this child's session (and an unfinished match for their teammate). */
export async function leaveRoom(session: GuestSession): Promise<void> {
  try {
    await request('/api/v1/session/leave', { method: 'POST', token: session.guest_session_token });
  } finally {
    clearGuestSession();
  }
}

/** Load a picture the server authorized for this child, as a local object URL. */
export async function fetchPicture(session: GuestSession, url: string): Promise<string> {
  const response = await fetch(url, { headers: { Authorization: `Bearer ${session.guest_session_token}` } });
  if (!response.ok) throw new ApiError('picture_unavailable', 'The picture is not available.');
  return URL.createObjectURL(await response.blob());
}
