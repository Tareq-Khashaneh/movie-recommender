"""Everything that reads or writes the `movies` table.

* load_movies_frame()  - SQLite -> a DataFrame shaped exactly like db.csv, so
                         catalog.py and reommender.py keep working unchanged.
* import_csv()         - one-time db.csv -> SQLite migration.
* upsert_movies()      - insert/update/link movies coming from TMDB.
"""
import json
import math
import re
import sqlite3
import unicodedata
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from app.database.connection import CSV_PATH, connect


class DatabaseNotReadyError(RuntimeError):
    """The database has no movies and there is no db.csv to import."""


@dataclass
class MovieRecord:
    """One movie in database form (already normalised by the TMDB mapping layer)."""

    tmdb_id: int
    title: str
    release_year: int
    rating: float
    vote_count: int = 0
    genres: str = ""
    overview: str | None = None
    release_date: str | None = None
    runtime_minutes: int | None = None
    poster_path: str | None = None
    poster_url: str | None = None
    backdrop_path: str | None = None
    director: str | None = None
    cast_names: list[str] = field(default_factory=list)
    gross: int | None = None


@dataclass
class UpsertStats:
    inserted: int = 0
    updated: int = 0
    linked: int = 0  # existing db.csv movies matched to their TMDB entry


# --------------------------------------------------------------------------- helpers
def _none(value):
    """NaN / pandas NA -> None, numpy scalars -> plain Python (sqlite3 needs both)."""
    if value is None or value is pd.NA:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def normalize_title(title: str) -> str:
    """'Léon: The Professional' -> 'leontheprofessional' (for matching only)."""
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", ascii_title.lower())


def count_movies(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]


# ----------------------------------------------------------------------- CSV -> SQLite
def import_csv(conn: sqlite3.Connection, csv_path=CSV_PATH) -> int:
    """Copy db.csv into an EMPTY movies table, keeping row numbers as ids.

    Refuses to touch a table that already has movies, so it can never
    overwrite synced data.
    """
    if count_movies(conn) > 0:
        raise RuntimeError("The movies table is not empty; refusing to import db.csv over it.")

    df = pd.read_csv(csv_path)
    rows = []
    for position, row in df.iterrows():
        runtime = re.search(r"\d+", str(_none(row["Runtime"]) or ""))
        gross = re.sub(r"\D", "", str(_none(row["Gross"]) or ""))
        year = pd.to_numeric(row["Released_Year"], errors="coerce")
        meta = _none(row["Meta_score"])
        cast = [s for s in (row["Star1"], row["Star2"], row["Star3"], row["Star4"])
                if isinstance(s, str) and s]
        rows.append(
            (
                int(position),  # API id == original CSV row number
                str(row["Series_Title"]),
                _none(row["Overview"]),
                None if pd.isna(year) else int(year),
                int(runtime.group()) if runtime else None,
                _none(row["Genre"]) or "",
                float(row["IMDB_Rating"]),
                int(row["No_of_Votes"]),
                _none(row["Poster_Link"]),
                _none(row["Certificate"]),
                None if meta is None else int(meta),
                _none(row["Director"]),
                json.dumps(cast),
                int(gross) if gross else None,
            )
        )
    with conn:
        conn.executemany(
            """INSERT INTO movies (id, title, overview, release_year, runtime_minutes, genres,
                                   rating, vote_count, poster_url, certificate, meta_score,
                                   director, cast_names, gross, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'csv')""",
            rows,
        )
    return len(rows)


def ensure_database(allow_empty: bool = False) -> None:
    """Make sure the database exists and has movies. Called when the API starts.

    First start with no movies.db: db.csv is imported automatically (nothing
    existing is ever deleted or overwritten). With no db.csv either, the API
    refuses to start (clear error), but the sync command passes allow_empty=True
    so it can fill the empty database from TMDB alone.
    """
    conn = connect()
    try:
        if count_movies(conn) == 0:
            if not CSV_PATH.exists():
                if allow_empty:
                    return
                raise DatabaseNotReadyError(
                    "The movie database is empty and data/db.csv was not found. "
                    "Run `python -m app.sync.sync_movies` (needs TMDB_API_KEY) to fill it."
                )
            import_csv(conn)
    finally:
        conn.close()


# ----------------------------------------------------------------------- SQLite -> frame
_COLUMNS = ["id", "title", "overview", "release_year", "runtime_minutes", "genres", "rating",
            "vote_count", "poster_url", "certificate", "meta_score", "director", "cast_names", "gross"]


def _text(values) -> pd.Series:
    """Text column with NaN (not None) for missing, like pandas.read_csv gives."""
    series = pd.Series(list(values), dtype=object)
    return series.where(series.notna(), np.nan)


def load_movies_frame() -> pd.DataFrame:
    """Return all movies as a DataFrame with the same columns/formats as db.csv.

    The index is the API-facing movie id. This is the compatibility layer:
    everything downstream (catalog.py, reommender.py) was written for the CSV
    shape and keeps working without changes.
    """
    ensure_database()
    conn = connect()
    try:
        rows = conn.execute(f"SELECT {', '.join(_COLUMNS)} FROM movies ORDER BY id").fetchall()
    finally:
        conn.close()

    df = pd.DataFrame([tuple(r) for r in rows], columns=_COLUMNS)
    cast = df["cast_names"].map(json.loads)

    years = pd.to_numeric(df["release_year"])
    frame = pd.DataFrame(
        {
            "Poster_Link": _text(df["poster_url"]),
            "Series_Title": _text(df["title"]),
            # int when every year is known (like read_csv); float with NaN otherwise
            "Released_Year": years.astype(int) if years.notna().all() else years.astype(float),
            "Certificate": _text(df["certificate"]),
            "Runtime": _text(
                f"{int(m)} min" if pd.notna(m) else np.nan for m in df["runtime_minutes"]
            ),
            "Genre": _text(g or np.nan for g in df["genres"]),
            "IMDB_Rating": df["rating"].astype(float),
            "Overview": _text(df["overview"]),
            "Meta_score": pd.to_numeric(df["meta_score"]).astype(float),
            "Director": _text(df["director"]),
            "Star1": _text(c[0] if len(c) > 0 else np.nan for c in cast),
            "Star2": _text(c[1] if len(c) > 1 else np.nan for c in cast),
            "Star3": _text(c[2] if len(c) > 2 else np.nan for c in cast),
            "Star4": _text(c[3] if len(c) > 3 else np.nan for c in cast),
            "No_of_Votes": df["vote_count"].astype(int),
            "Gross": _text(f"{int(g):,}" if pd.notna(g) else np.nan for g in df["gross"]),
        }
    )
    frame.index = pd.Index(df["id"].astype(int).to_numpy())
    return frame


# ---------------------------------------------------------------------- TMDB -> SQLite
def _find_legacy_match(index: dict, record: MovieRecord) -> int | None:
    """Find the db.csv movie (not yet linked to TMDB) that this TMDB movie is."""
    candidates = index.get(normalize_title(record.title), [])
    # exact year first, then +/- 1 year (release dates differ between sources)
    for tolerance in (0, 1):
        for movie_id, year in candidates:
            if year is not None and abs(year - record.release_year) <= tolerance:
                return movie_id
    return None


def upsert_movies(conn: sqlite3.Connection, records: list[MovieRecord]) -> UpsertStats:
    """Insert new movies, update known ones, never create duplicates.

    Everything happens in ONE transaction: if anything fails, the database is
    left exactly as it was. Movies are never deleted.

    Rules:
    * known tmdb_id                -> refresh the row
    * unlinked db.csv movie with the same title (+/-1 year) -> link it to TMDB
    * otherwise                    -> insert with a fresh id
    db.csv movies are updated conservatively: they keep their IMDb rating,
    votes, title and genres (TMDB has no 'Biography'/'Film-Noir'/'Sport'...), and
    only gain a sharper TMDB poster plus any field that was empty.
    """
    stats = UpsertStats()
    legacy_index: dict[str, list[tuple[int, int | None]]] = {}
    for row in conn.execute("SELECT id, title, release_year FROM movies WHERE tmdb_id IS NULL"):
        legacy_index.setdefault(normalize_title(row["title"]), []).append((row["id"], row["release_year"]))

    with conn:
        for record in records:
            cast_json = json.dumps(record.cast_names)
            existing = conn.execute(
                "SELECT id, source FROM movies WHERE tmdb_id = ?", (record.tmdb_id,)
            ).fetchone()
            linked_now = False

            if existing is None:
                legacy_id = _find_legacy_match(legacy_index, record)
                if legacy_id is not None:
                    existing = {"id": legacy_id, "source": "csv"}
                    legacy_index[normalize_title(record.title)] = [
                        c for c in legacy_index[normalize_title(record.title)] if c[0] != legacy_id
                    ]
                    linked_now = True
                    stats.linked += 1

            if existing is None:
                conn.execute(
                    """INSERT INTO movies (tmdb_id, title, overview, release_date, release_year,
                           runtime_minutes, genres, rating, vote_count, poster_path, poster_url,
                           backdrop_path, director, cast_names, gross, source)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'tmdb')""",
                    (record.tmdb_id, record.title, record.overview, record.release_date,
                     record.release_year, record.runtime_minutes, record.genres, record.rating,
                     record.vote_count, record.poster_path, record.poster_url,
                     record.backdrop_path, record.director, cast_json, record.gross),
                )
                stats.inserted += 1
            elif existing["source"] == "csv":
                conn.execute(
                    """UPDATE movies SET tmdb_id = ?,
                           poster_path   = COALESCE(?, poster_path),
                           poster_url    = COALESCE(?, poster_url),
                           backdrop_path = COALESCE(?, backdrop_path),
                           overview      = COALESCE(overview, ?),
                           release_date  = COALESCE(release_date, ?),
                           runtime_minutes = COALESCE(runtime_minutes, ?),
                           director      = COALESCE(director, ?),
                           gross         = COALESCE(gross, ?),
                           genres        = CASE WHEN genres = '' THEN ? ELSE genres END,
                           cast_names    = CASE WHEN cast_names = '[]' THEN ? ELSE cast_names END,
                           updated_at    = datetime('now')
                       WHERE id = ?""",
                    (record.tmdb_id, record.poster_path, record.poster_url, record.backdrop_path,
                     record.overview, record.release_date, record.runtime_minutes, record.director,
                     record.gross, record.genres, cast_json, existing["id"]),
                )
                if not linked_now:
                    stats.updated += 1
            else:
                conn.execute(
                    """UPDATE movies SET title = ?, overview = ?, release_date = ?, release_year = ?,
                           genres = ?, rating = ?, vote_count = ?,
                           poster_path   = COALESCE(?, poster_path),
                           poster_url    = COALESCE(?, poster_url),
                           backdrop_path = COALESCE(?, backdrop_path),
                           runtime_minutes = COALESCE(?, runtime_minutes),
                           director      = COALESCE(?, director),
                           gross         = COALESCE(?, gross),
                           cast_names    = CASE WHEN ? = '[]' THEN cast_names ELSE ? END,
                           updated_at    = datetime('now')
                       WHERE id = ?""",
                    (record.title, record.overview, record.release_date, record.release_year,
                     record.genres, record.rating, record.vote_count, record.poster_path,
                     record.poster_url, record.backdrop_path, record.runtime_minutes,
                     record.director, record.gross, cast_json, cast_json, existing["id"]),
                )
                stats.updated += 1
    return stats
