-- D2: transcribed hold-to-talk clips and the AI feedback result of each round.
-- Audio is never stored here: it is deleted as soon as Whisper has turned it into text.

create table public.clips (
  clip_id text primary key,
  round_id text not null references public.rounds (round_id),
  player_id text not null references public.players (player_id),
  role text not null check (role in ('speaker', 'drawer')),
  status text not null check (status in ('pending', 'done', 'failed')),
  text text,
  created_at timestamptz not null default now()
);

create index clips_round_idx on public.clips (round_id, created_at);

-- Set once when the round leaves checking: stars and lines per role, or null for the neutral result.
alter table public.rounds add column result jsonb;

alter table public.clips enable row level security;
