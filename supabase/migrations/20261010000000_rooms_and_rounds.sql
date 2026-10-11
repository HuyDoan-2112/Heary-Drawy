-- Feature 02: guest rooms, pairing, and round authority.
-- Server-private tables. Row level security is enabled with no policies so the
-- Supabase anon/authenticated API roles cannot read them; the FastAPI service
-- connects with a server credential and enforces authorization itself.

create table public.rooms (
  room_id text primary key,
  admission_status text not null check (admission_status in ('open', 'closed')),
  expires_at timestamptz not null,
  created_at timestamptz not null default now()
);

create table public.players (
  player_id text primary key,
  room_id text not null references public.rooms (room_id),
  nickname text not null,
  normalized_nickname text not null,
  avatar_id text not null,
  membership_status text not null check (membership_status in ('admitted', 'removed')),
  created_at timestamptz not null default now(),
  constraint players_room_nickname_key unique (room_id, normalized_nickname)
);

create table public.guest_sessions (
  session_id text primary key,
  player_id text not null references public.players (player_id),
  room_id text not null references public.rooms (room_id),
  token_hash text not null unique,
  expires_at timestamptz not null,
  revoked_at timestamptz
);

create table public.pairs (
  pair_id text primary key,
  room_id text not null references public.rooms (room_id),
  -- Roles are randomized once per match; later rounds swap them.
  initial_speaker_player_id text not null references public.players (player_id),
  initial_drawer_player_id text not null references public.players (player_id),
  current_round_id text,
  created_at timestamptz not null default now(),
  check (initial_speaker_player_id <> initial_drawer_player_id)
);

-- A player belongs to at most one pair; a pair has exactly two seats.
create table public.pair_members (
  player_id text primary key references public.players (player_id),
  pair_id text not null references public.pairs (pair_id),
  seat smallint not null check (seat in (1, 2)),
  unique (pair_id, seat)
);

create table public.rounds (
  round_id text primary key,
  pair_id text not null references public.pairs (pair_id),
  round_index integer not null check (round_index >= 1),
  phase text not null check (phase in
    ('role_intro', 'collaborating', 'finalizing', 'feedback', 'exploring', 'finished')),
  phase_version integer not null check (phase_version >= 1),
  speaker_player_id text not null references public.players (player_id),
  drawer_player_id text not null references public.players (player_id),
  drawing_revision integer not null default 0 check (drawing_revision >= 0),
  created_at timestamptz not null default now(),
  unique (pair_id, round_index),
  check (speaker_player_id <> drawer_player_id)
);

alter table public.pairs
  add constraint pairs_current_round_fkey foreign key (current_round_id)
  references public.rounds (round_id) deferrable initially deferred;

create table public.intro_seen (
  round_id text not null references public.rounds (round_id),
  player_id text not null references public.players (player_id),
  primary key (round_id, player_id)
);

create table public.play_again_intents (
  round_id text not null references public.rounds (round_id),
  player_id text not null references public.players (player_id),
  primary key (round_id, player_id)
);

-- Command identity is scoped to the authenticated player.
create table public.commands (
  player_id text not null references public.players (player_id),
  command_id text not null,
  payload_hash text not null,
  response jsonb not null,
  created_at timestamptz not null default now(),
  primary key (player_id, command_id)
);

create index players_room_created_idx on public.players (room_id, created_at, player_id);
create index guest_sessions_player_idx on public.guest_sessions (player_id);

alter table public.rooms enable row level security;
alter table public.players enable row level security;
alter table public.guest_sessions enable row level security;
alter table public.pairs enable row level security;
alter table public.pair_members enable row level security;
alter table public.rounds enable row level security;
alter table public.intro_seen enable row level security;
alter table public.play_again_intents enable row level security;
alter table public.commands enable row level security;
