"""TMDB sync tests.

No real TMDB access is used (or needed) here: a fake TMDB feeds canned JSON in the
documented TMDB response shapes, so parsing, normalisation, the database
upsert logic, retries and failure handling are all exercised locally. A live
sync against the real TMDB has to be run by you with your own API key.
"""
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from app.database.connection import connect
from app.database.movie_store import count_movies, import_csv
from app.services import tmdb
from app.services.tmdb import (
    MissingApiKeyError,
    TMDBAuthError,
    TMDBClient,
    TMDBRequestError,
    normalize_movie,
)
from app.sync import sync_movies
from app.sync.sync_movies import SyncError, run_sync

GENRES = [{"id": 28, "name": "Action"}, {"id": 878, "name": "Science Fiction"},
          {"id": 18, "name": "Drama"}, {"id": 80, "name": "Crime"}]
GENRE_MAP = {g["id"]: g["name"] for g in GENRES}


def _item(tmdb_id, title, date, genre_ids, avg, votes, poster="/p.jpg", **extra):
    return {"id": tmdb_id, "title": title, "release_date": date, "genre_ids": genre_ids,
            "vote_average": avg, "vote_count": votes, "poster_path": poster,
            "overview": f"About {title}.", "adult": False, **extra}


LIST_ITEMS = [
    _item(238, "The Godfather", "1972-03-14", [18, 80], 8.7, 21000, "/godfather_tmdb.jpg"),  # in db.csv
    _item(900001, "Future Quest", "2026-09-12", [28, 878], 7.34, 150, "/fq.jpg"),
    _item(900002, "No Poster Movie", "2026-01-01", [18], 6.0, 80, None),
    _item(900003, "Adult Thing", "2026-01-01", [18], 6.0, 500, adult=True),
    _item(900004, "No Genres", "2026-01-01", [], 6.0, 500),
    _item(900005, "Hardly Voted", "2026-01-01", [18], 9.9, 3),
]
DETAILS = {
    238: {"id": 238, "runtime": 175, "revenue": 245066411,
          "genres": [{"id": 18, "name": "Drama"}, {"id": 80, "name": "Crime"}],
          "credits": {"cast": [{"name": "Marlon Brando", "order": 0}],
                      "crew": [{"name": "Francis Ford Coppola", "job": "Director"}]}},
    900001: {"id": 900001, "runtime": 128, "revenue": 0,
             "genres": [{"id": 28, "name": "Action"}, {"id": 878, "name": "Science Fiction"}],
             "credits": {"cast": [{"name": f"Actor {n}", "order": n} for n in (4, 2, 0, 1, 3)],
                         "crew": [{"name": "Some Editor", "job": "Editor"},
                                  {"name": "Dana Director", "job": "Director"}]}},
    900002: {"id": 900002, "runtime": 0, "revenue": 0, "genres": [{"id": 18, "name": "Drama"}],
             "credits": {"cast": [], "crew": []}},
}


class FakeTMDB:
    """Callable with the same signature as the client's fetch function."""

    def __init__(self):
        self.items = [dict(i) for i in LIST_ITEMS]
        self.status_for = {}  # path prefix -> HTTP status to answer instead
        self.calls = []

    def __call__(self, url, headers, timeout):
        parsed = urlparse(url)
        path = parsed.path.removeprefix("/3")
        self.calls.append(path)
        for prefix, status in self.status_for.items():
            if path.startswith(prefix):
                return status, {}, b"{}"
        if path == "/genre/movie/list":
            return 200, {}, json.dumps({"genres": GENRES}).encode()
        if path in ("/movie/top_rated", "/movie/popular", "/movie/now_playing"):
            page = int(parse_qs(parsed.query)["page"][0])
            results = self.items if (path == "/movie/top_rated" and page == 1) else []
            return 200, {}, json.dumps({"results": results, "total_pages": 1}).encode()
        movie_id = int(path.rsplit("/", 1)[1])
        if movie_id in DETAILS:
            return 200, {}, json.dumps(DETAILS[movie_id]).encode()
        return 404, {}, b"{}"


def make_client(fake):
    return TMDBClient("test-key", fetch=fake, sleep=lambda s: None, base_url="http://fake/3")


@pytest.fixture
def conn(tmp_path):
    connection = connect(tmp_path / "movies.db")
    import_csv(connection)
    yield connection
    connection.close()


def snapshot(conn):
    return [tuple(r) for r in conn.execute("SELECT * FROM movies ORDER BY id")]


# ------------------------------------------------------------------ mapping layer
def test_normalize_maps_tmdb_fields_to_our_format():
    record = normalize_movie(LIST_ITEMS[1], DETAILS[900001], GENRE_MAP)
    assert record.tmdb_id == 900001
    assert record.title == "Future Quest"
    assert record.release_year == 2026 and record.release_date == "2026-09-12"
    assert record.genres == "Action, Sci-Fi"          # "Science Fiction" -> app vocabulary
    assert record.rating == 7.3 and record.vote_count == 150
    assert record.poster_url == "https://image.tmdb.org/t/p/w500/fq.jpg"
    assert record.poster_path == "/fq.jpg"
    assert record.runtime_minutes == 128
    assert record.director == "Dana Director"
    assert record.cast_names == ["Actor 0", "Actor 1", "Actor 2", "Actor 3"]  # top 4 by billing order
    assert record.gross is None                        # TMDB reports 0 when unknown


def test_normalize_works_from_list_data_only_and_skips_unusable_movies():
    record = normalize_movie(LIST_ITEMS[1], None, GENRE_MAP)
    assert record.genres == "Action, Sci-Fi" and record.runtime_minutes is None
    assert normalize_movie(LIST_ITEMS[2], None, GENRE_MAP).poster_url is None
    assert normalize_movie(LIST_ITEMS[3], None, GENRE_MAP) is None   # adult
    assert normalize_movie(LIST_ITEMS[4], None, GENRE_MAP) is None   # no genres
    assert normalize_movie(_item(1, "x", "", [18], 5, 50), None, GENRE_MAP) is None  # no date


# ----------------------------------------------------------------------- the sync
def test_sync_inserts_new_movies_and_links_existing_ones(conn):
    godfather = conn.execute("SELECT * FROM movies WHERE title = 'The Godfather'").fetchone()
    report = run_sync(make_client(FakeTMDB()), conn, log=lambda *_: None)

    assert (report.inserted, report.linked) == (2, 1)          # Future Quest, No Poster Movie / Godfather
    assert count_movies(conn) == 1002

    # new movies got ids 1000, 1001 - the old ids are untouched
    new_ids = [r[0] for r in conn.execute("SELECT id FROM movies WHERE source = 'tmdb' ORDER BY id")]
    assert new_ids == [1000, 1001]

    linked = conn.execute("SELECT * FROM movies WHERE id = ?", (godfather["id"],)).fetchone()
    assert linked["tmdb_id"] == 238 and linked["source"] == "csv"
    assert linked["poster_url"] == "https://image.tmdb.org/t/p/w500/godfather_tmdb.jpg"  # sharper poster
    assert linked["rating"] == godfather["rating"]            # keeps its IMDb rating
    assert linked["genres"] == godfather["genres"]            # keeps its genres
    assert linked["title"] == godfather["title"]

    # skipped: adult, no genres, too few votes
    assert conn.execute("SELECT COUNT(*) FROM movies WHERE tmdb_id IN (900003, 900004, 900005)").fetchone()[0] == 0


def test_running_sync_twice_creates_no_duplicates(conn):
    fake = FakeTMDB()
    run_sync(make_client(fake), conn, log=lambda *_: None)
    first = snapshot(conn)
    report = run_sync(make_client(fake), conn, log=lambda *_: None)
    assert (report.inserted, report.linked) == (0, 0)
    assert count_movies(conn) == 1002
    tmdb_ids = [r[0] for r in conn.execute("SELECT tmdb_id FROM movies WHERE tmdb_id IS NOT NULL")]
    assert len(tmdb_ids) == len(set(tmdb_ids)) == 3
    # nothing but updated_at may differ between the two runs
    assert [r[:-1] for r in snapshot(conn)] == [r[:-1] for r in first]


def test_sync_updates_changed_movies_in_place(conn):
    fake = FakeTMDB()
    run_sync(make_client(fake), conn, log=lambda *_: None)
    fake.items[1] = dict(fake.items[1], vote_average=8.8, vote_count=900, title="Future Quest II")
    report = run_sync(make_client(fake), conn, log=lambda *_: None)
    row = conn.execute("SELECT * FROM movies WHERE tmdb_id = 900001").fetchone()
    assert row["id"] == 1000                                   # same API id
    assert (row["title"], row["rating"], row["vote_count"]) == ("Future Quest II", 8.8, 900)
    assert row["director"] == "Dana Director"                  # details survive
    assert report.inserted == 0 and report.updated >= 1


def test_without_details_new_movies_still_sync_from_list_data(conn):
    fake = FakeTMDB()
    run_sync(make_client(fake), conn, with_details=False, log=lambda *_: None)
    assert not [c for c in fake.calls if c.startswith("/movie/9") or c == "/movie/238"]
    row = conn.execute("SELECT * FROM movies WHERE tmdb_id = 900001").fetchone()
    assert row["genres"] == "Action, Sci-Fi" and row["runtime_minutes"] is None


def test_dry_run_writes_nothing(conn):
    before = snapshot(conn)
    report = run_sync(make_client(FakeTMDB()), conn, dry_run=True, log=lambda *_: None)
    assert report.candidates == 3 and snapshot(conn) == before


# ---------------------------------------------------------------- failure handling
def test_tmdb_outage_leaves_the_database_untouched(conn):
    before = snapshot(conn)
    fake = FakeTMDB()
    fake.status_for = {"/": 503}
    with pytest.raises(TMDBRequestError):
        run_sync(make_client(fake), conn, log=lambda *_: None)
    assert snapshot(conn) == before


def test_empty_tmdb_answer_is_an_error_not_a_wipe(conn):
    before = snapshot(conn)
    fake = FakeTMDB()
    fake.items = []
    with pytest.raises(SyncError):
        run_sync(make_client(fake), conn, log=lambda *_: None)
    assert snapshot(conn) == before


def test_invalid_api_key_stops_with_a_clear_error_and_changes_nothing(conn):
    before = snapshot(conn)
    fake = FakeTMDB()
    fake.status_for = {"/": 401}
    with pytest.raises(TMDBAuthError, match="TMDB_API_KEY"):
        run_sync(make_client(fake), conn, log=lambda *_: None)
    assert snapshot(conn) == before


def test_failed_detail_lookup_keeps_the_movie_using_list_data(conn):
    fake = FakeTMDB()
    fake.status_for = {"/movie/900001": 500}
    report = run_sync(make_client(fake), conn, log=lambda *_: None)
    assert report.detail_failures == 1
    row = conn.execute("SELECT * FROM movies WHERE tmdb_id = 900001").fetchone()
    assert row is not None and row["runtime_minutes"] is None and row["genres"] == "Action, Sci-Fi"


def test_a_failing_later_list_page_keeps_what_was_already_fetched(conn):
    fake = FakeTMDB()
    fake.status_for = {"/movie/popular": 500}
    report = run_sync(make_client(fake), conn, log=lambda *_: None)
    assert report.inserted == 2 and any("popular" in w for w in report.warnings)


def test_missing_api_key_gives_a_clear_error(monkeypatch, capsys):
    monkeypatch.setattr(tmdb, "load_env_file", lambda *a, **k: None)
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    with pytest.raises(MissingApiKeyError, match="TMDB_API_KEY"):
        tmdb.get_api_key()
    assert sync_movies.main([]) == 2
    assert "TMDB_API_KEY is not set" in capsys.readouterr().out


def test_api_key_is_read_from_the_environment_and_dotenv(monkeypatch, tmp_path):
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text('# comment\nTMDB_API_KEY="abc123"\n')
    tmdb.load_env_file(env_file)
    assert tmdb.get_api_key() == "abc123"
    monkeypatch.delenv("TMDB_API_KEY")


# ------------------------------------------------- real HTTP code path (local server)
class _Handler(BaseHTTPRequestHandler):
    hits = 0

    def do_GET(self):  # noqa: N802
        type(self).hits += 1
        if self.path.startswith("/3/genre/movie/list") and type(self).hits == 1:
            self.send_response(500)  # first call fails -> client must retry
            self.end_headers()
            return
        body = json.dumps({"genres": GENRES}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def test_real_http_requests_retry_after_a_server_error():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        _Handler.hits = 0
        client = TMDBClient("k", sleep=lambda s: None, base_url=f"http://127.0.0.1:{server.server_port}/3")
        assert client.genre_map()[878] == "Science Fiction"
        assert _Handler.hits == 2  # one failure + one successful retry
    finally:
        server.shutdown()


# ----------------------------------------- end to end: API serves the synced movies
def test_api_serves_synced_movies_and_keeps_old_ids(tmp_path):
    db = tmp_path / "synced.db"
    connection = connect(db)
    import_csv(connection)
    run_sync(make_client(FakeTMDB()), connection, log=lambda *_: None)
    connection.close()

    script = """
import json
from fastapi.testclient import TestClient
from app.main import app
c = TestClient(app)
out = {}
out["health"] = c.get("/health").json()
out["new"] = c.get("/movies/1000").json()
out["new_no_runtime"] = c.get("/movies/1001").json()
out["old"] = c.get("/movies/0").json()["title"]
out["listing_total"] = c.get("/movies", params={"search": "future quest"}).json()["total"]
out["genres_has_scifi"] = "Sci-Fi" in c.get("/movies/genres").json()
rec = c.post("/recommendations", json={"movie_ids": [1000, 1001, 0]})
out["rec_status"] = rec.status_code
out["rec_has_unique_ids"] = len({i["id"] for i in rec.json()["items"]}) == len(rec.json()["items"])
legacy = c.post("/recommend", json=["Future Quest", "No Poster Movie"])
out["legacy_status"] = legacy.status_code
out["legacy_ok_json"] = isinstance(legacy.json()["recommendations"], list)
print(json.dumps(out))
"""
    import os
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True,
        cwd=Path(__file__).resolve().parent.parent,
        env={**os.environ, "MOVIES_DB_PATH": str(db)},
    )
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout.strip().splitlines()[-1])
    assert out["health"] == {"status": "ok", "movies": 1002}
    assert out["old"] == "The Shawshank Redemption"
    assert out["new"]["title"] == "Future Quest" and out["new"]["director"] == "Dana Director"
    assert out["new"]["poster_url"] == "https://image.tmdb.org/t/p/w500/fq.jpg"
    assert set(out["new"]) == {"id", "title", "poster_url", "year", "genres", "imdb_rating", "certificate",
                               "runtime_minutes", "overview", "meta_score", "director", "cast", "votes", "gross"}
    assert out["new_no_runtime"]["runtime_minutes"] is None and out["new_no_runtime"]["poster_url"] is None
    assert out["listing_total"] == 1 and out["genres_has_scifi"] is True
    assert out["rec_status"] == 200 and out["rec_has_unique_ids"] is True
    assert out["legacy_status"] == 200 and out["legacy_ok_json"] is True


# ------------------------------------- fresh start without db.csv (sync fills an empty DB)
def test_sync_can_fill_an_empty_database_when_db_csv_is_missing(monkeypatch, tmp_path, capsys):
    from app.database import movie_store

    db = tmp_path / "fresh.db"
    monkeypatch.setenv("MOVIES_DB_PATH", str(db))
    monkeypatch.setattr(movie_store, "CSV_PATH", tmp_path / "missing.csv")
    monkeypatch.setattr(sync_movies, "get_api_key", lambda: "k")
    monkeypatch.setattr(sync_movies, "TMDBClient", lambda key: make_client(FakeTMDB()))

    # the API itself must still refuse to start on an empty database, with a clear message
    with pytest.raises(movie_store.DatabaseNotReadyError, match="sync_movies"):
        movie_store.ensure_database()

    assert sync_movies.main(["--pages", "1"]) == 0
    assert "inserted 3" in capsys.readouterr().out
    connection = connect(db)
    try:
        assert count_movies(connection) == 3
    finally:
        connection.close()
    movie_store.ensure_database()  # database is now ready: no error
