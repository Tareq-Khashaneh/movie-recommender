# Movie Recommender API

FastAPI backend: genre-based movie recommendations (TF-IDF + cosine similarity).
Movies live in **SQLite** and can be refreshed from **TMDB**.

## Run
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0
```
On the first start, `data/movies.db` is created automatically from `data/db.csv`
(1000 movies, ids 0-999). `db.csv` is only the starting data and a backup: once
`movies.db` exists the API never reads it, but keep it in the repo so a fresh clone can
start (and because the test-suite compares against it). Without `db.csv` a fresh clone
must run the TMDB sync first, which then fills the database from TMDB alone.

## Keep the movie database up to date (TMDB)
1. Get a free API key: https://www.themoviedb.org/settings/api
2. Provide it as an environment variable (never commit it):
   - Windows PowerShell: `$env:TMDB_API_KEY="your_key"`  (this window only)
     or `setx TMDB_API_KEY "your_key"` (permanent, then open a new terminal)
   - macOS/Linux: `export TMDB_API_KEY=your_key`
   - or copy `.env.example` to `.env` and fill it in.
3. First sync: `python -m app.sync.sync_movies --pages 10`
4. Later syncs: `python -m app.sync.sync_movies`
5. **Restart the API server** so it loads the new movies.

Useful options: `--dry-run` (fetch and report, write nothing), `--no-details` (faster,
skips runtime/director/cast for new movies), `--sources top_rated,popular,now_playing,upcoming`,
`--min-votes 20`.

The sync is safe by design: it fetches everything first, then writes in one transaction;
it never deletes movies; running it twice creates no duplicates; if TMDB is down or the key
is wrong the database stays exactly as it was.

## API ids
`id` is permanent. The original 1000 movies keep ids 0-999; new movies get 1000, 1001, ...
(ids are never reused). TMDB's own id is stored separately in `tmdb_id`.

## Tests
```bash
pip install -r requirements-dev.txt
pytest
```
`tests/test_golden_api_contract.py` replays 1159 recorded requests from the original CSV-based
API and requires identical JSON. The tests use a temporary database, never your `movies.db`.

---
This product uses the TMDB API but is not endorsed or certified by TMDB.
