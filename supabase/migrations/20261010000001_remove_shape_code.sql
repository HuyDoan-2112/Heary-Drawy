-- Retire shape-code admission from earlier local databases. A fresh database
-- already has the final no-code schema in 20261010000000_rooms_and_rounds.sql.
drop index if exists public.rooms_active_shape_code_key;
alter table public.rooms drop column if exists shape_code;
