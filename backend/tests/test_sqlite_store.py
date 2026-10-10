import pandas as pd
import pytest

from app.database.connection import CSV_PATH, connect
from app.database.movie_store import (
    MovieRecord,
    count_movies,
    import_csv,
    load_movies_frame,
    upsert_movies,
)


@pytest.fixture
def conn(tmp_path):
    connection = connect(tmp_path / "movies.db")
    yield connection
    connection.close()


def test_csv_import_keeps_row_numbers_as_ids(conn):
    assert import_csv(conn) == 1000
    csv = pd.read_csv(CSV_PATH)
    ids = [r["id"] for r in conn.execute("SELECT id FROM movies ORDER BY id")]
    assert ids == list(range(1000))
    assert conn.execute("SELECT title FROM movies WHERE id = 966").fetchone()[0] == "Apollo 13"
    assert conn.execute("SELECT title FROM movies WHERE id = 87").fetchone()[0] == csv.loc[87, "Series_Title"]


def test_import_refuses_to_overwrite_existing_data(conn):
    import_csv(conn)
    with pytest.raises(RuntimeError):
        import_csv(conn)
    assert count_movies(conn) == 1000


def test_database_frame_matches_the_csv_column_by_column():
    """SQLite -> frame must reproduce db.csv exactly (this is what keeps the API unchanged)."""
    frame = load_movies_frame().reset_index(drop=True)
    csv = pd.read_csv(CSV_PATH)
    assert list(frame.columns) == list(csv.columns)
    for column in csv.columns:
        pd.testing.assert_series_equal(
            frame[column].astype(object), csv[column].astype(object),
            check_names=False, check_dtype=False, obj=column,
        )
    assert frame.dtypes["Released_Year"] == csv.dtypes["Released_Year"]


def test_new_movies_get_new_ids_and_old_ids_never_change(conn):
    import_csv(conn)
    before = [tuple(r) for r in conn.execute("SELECT id, title, rating FROM movies ORDER BY id")]
    stats = upsert_movies(conn, [
        MovieRecord(tmdb_id=777001, title="Brand New Film", release_year=2026, rating=7.1,
                    vote_count=50, genres="Drama"),
    ])
    assert (stats.inserted, stats.updated, stats.linked) == (1, 0, 0)
    assert conn.execute("SELECT id FROM movies WHERE tmdb_id = 777001").fetchone()[0] == 1000
    after = [tuple(r) for r in conn.execute("SELECT id, title, rating FROM movies WHERE id < 1000 ORDER BY id")]
    assert after == before
