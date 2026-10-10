"""SQLite location and schema.

The database file is data/movies.db (override with the MOVIES_DB_PATH
environment variable). `data/db.csv` is kept only as the one-time import
source / backup.
"""
import os
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "db.csv"

SCHEMA = """
CREATE TABLE IF NOT EXISTS movies (
    -- API-facing id. Rows imported from db.csv keep their original row number
    -- (0..999) so the ids Flutter already knows never change; new movies get
    -- 1000, 1001, ... and ids are never reused.
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tmdb_id         INTEGER UNIQUE,            -- NULL until a row is linked to TMDB
    title           TEXT NOT NULL,
    overview        TEXT,
    release_date    TEXT,                      -- 'YYYY-MM-DD' when known
    release_year    INTEGER,
    runtime_minutes INTEGER,
    genres          TEXT NOT NULL DEFAULT '',  -- 'Drama, Crime' (same format as db.csv)
    rating          REAL NOT NULL,             -- IMDb rating (csv rows) / TMDB average (new rows)
    vote_count      INTEGER NOT NULL DEFAULT 0,
    poster_path     TEXT,                      -- TMDB path, e.g. '/abc.jpg'
    poster_url      TEXT,                      -- full URL returned by the API
    backdrop_path   TEXT,
    certificate     TEXT,
    meta_score      INTEGER,
    director        TEXT,
    cast_names      TEXT NOT NULL DEFAULT '[]',  -- JSON list, top 4 actors
    gross           INTEGER,
    source          TEXT NOT NULL DEFAULT 'tmdb',  -- 'csv' (imported) or 'tmdb' (synced)
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_movies_title_year ON movies (title COLLATE NOCASE, release_year);
"""


def get_db_path() -> Path:
    override = os.environ.get("MOVIES_DB_PATH")
    return Path(override) if override else PROJECT_ROOT / "data" / "movies.db"


def connect(path: Path | str | None = None) -> sqlite3.Connection:
    """Open the database (creating the file and tables if they do not exist yet)."""
    db_path = Path(path) if path else get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
