CREATE TABLE IF NOT EXISTS users (
    id    SERIAL PRIMARY KEY,
    name  TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS accounts (
    id            SERIAL PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    display_name  TEXT,
    password_hash TEXT,
    provider      TEXT NOT NULL DEFAULT 'local',
    google_sub    TEXT UNIQUE
);
