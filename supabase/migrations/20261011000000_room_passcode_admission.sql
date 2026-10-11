-- Feature 02: grown-up passcode admission, match end, and retention support.
--
-- A grown-up unlocks a device with the Room passcode (only its hash is stored). The device
-- enrollment then admits children on that device. Nicknames and characters are unique among
-- the Room's currently admitted players, so a child who leaves frees both.

alter table public.rooms
  add column host_passcode_hash text,
  add column closed_at timestamptz;

create unique index rooms_host_passcode_hash_key on public.rooms (host_passcode_hash)
  where host_passcode_hash is not null;

create table public.device_enrollments (
  device_id text primary key,
  room_id text not null references public.rooms (room_id),
  token_hash text not null unique,
  expires_at timestamptz not null,
  revoked_at timestamptz,
  -- The child currently playing on this device; re-admitting releases them first.
  current_player_id text references public.players (player_id),
  created_at timestamptz not null default now()
);

create index device_enrollments_room_idx on public.device_enrollments (room_id);

alter table public.players drop constraint players_room_nickname_key;
create unique index players_room_nickname_key on public.players (room_id, normalized_nickname)
  where membership_status = 'admitted';
create unique index players_room_avatar_key on public.players (room_id, avatar_id)
  where membership_status = 'admitted';

alter table public.pairs
  add column ended_at timestamptz,
  add column end_reason text check (end_reason in ('completed', 'left')),
  add constraint pairs_end_consistent check ((ended_at is null) = (end_reason is null));

alter table public.device_enrollments enable row level security;

-- Feature 03/04 demo slice: each round's secret picture and its retained strokes.
alter table public.rounds
  add column object_id text,
  add column strokes jsonb not null default '[]'::jsonb;
