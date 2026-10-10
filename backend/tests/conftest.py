"""Run the whole test-suite against a throw-away SQLite database.

Set BEFORE any test module imports the app, so tests never touch (or depend on)
your real data/movies.db - even after you have synced new movies from TMDB.
The temp database is created from db.csv on first use, exactly like a fresh install.
"""
import os
import tempfile

os.environ["MOVIES_DB_PATH"] = os.path.join(
    tempfile.mkdtemp(prefix="movie-api-tests-"), "movies_test.db"
)
