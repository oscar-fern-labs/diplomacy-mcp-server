CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS games (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code TEXT UNIQUE NOT NULL,
  name TEXT,
  status TEXT NOT NULL DEFAULT lobby,
  map TEXT NOT NULL DEFAULT classic,
  phase_index INTEGER NOT NULL DEFAULT 0,
  current_phase JSONB NOT NULL DEFAULT {},
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS players (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  power TEXT,
  token TEXT NOT NULL,
  ready BOOLEAN NOT NULL DEFAULT false,
  joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (game_id, name),
  UNIQUE (game_id, power)
);

CREATE INDEX IF NOT EXISTS players_game_idx ON players(game_id);

CREATE TABLE IF NOT EXISTS phases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
  season TEXT NOT NULL,
  year INTEGER NOT NULL,
  phase_type TEXT NOT NULL,
  index_in_game INTEGER NOT NULL,
  board_state JSONB NOT NULL,
  orders JSONB NOT NULL DEFAULT [],
  results JSONB,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS phases_game_idx ON phases(game_id);

CREATE TABLE IF NOT EXISTS messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
  sender_player_id UUID REFERENCES players(id) ON DELETE SET NULL,
  recipients JSONB NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS messages_game_idx ON messages(game_id);
