# Movie Recommender 🎬

A content-based movie recommendation project with a **Flutter mobile
app** and a **FastAPI backend**. Users select five movies they like and
receive ten similar recommendations.

The backend calculates similarity using **TF-IDF on movie genres** and
**cosine similarity**. Movie data is stored in SQLite and can be
refreshed from **The Movie Database (TMDB)**.

## Features

### Flutter App

-   Browse the movie catalog with infinite scrolling.
-   Search by title, director, or cast, with debounced search.
-   Filter by genre and sort the catalog.
-   Select exactly five movies, with a live selection counter and
    removable thumbnails.
-   View ten recommendations with match badges.
-   Open a movie details screen with information such as overview,
    runtime, cast, votes, and box office.
-   Handle loading, empty, and error states, including retry, timeout,
    offline, and invalid-response cases.

### Backend API

-   REST API built with FastAPI.
-   Content-based recommendations using TF-IDF and cosine similarity.
-   SQLite database for movie data.
-   Optional TMDB synchronization to add and refresh movie data.
-   Stable API movie IDs: the original 1,000 movies use IDs `0–999`; new
    movies receive IDs starting at `1000`.
-   Tests for the API contract and recommendation behavior.

## Tech Stack

**Frontend** - Flutter - Dart - Riverpod 3 - Dio - Feature-first Clean
Architecture

**Backend** - Python - FastAPI - SQLite - TF-IDF and cosine similarity -
TMDB API

## Project Structure

``` text
movie-recommender/
├── backend/
│   ├── app/
│   ├── data/
│   ├── tests/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── README.md
├── movie_recommender/
│   ├── lib/
│   ├── test/
│   └── README.md
├── .gitignore
└── README.md
```

The exact contents may vary depending on your local project files. The
backend and Flutter folders each have their own README with
component-specific instructions.

## Getting Started

### 1. Run the Backend

Open a terminal in the `backend/` directory and install the
dependencies:

``` bash
pip install -r requirements.txt
```

Start the API:

``` bash
uvicorn app.main:app --reload --host 0.0.0.0
```

On the first start, the backend automatically creates `data/movies.db`
from `data/db.csv`. Keep `db.csv` in the repository so a fresh clone can
initialize its database.

### 2. Run the Flutter App

In another terminal, open the `movie_recommender/` directory and run:

``` bash
flutter pub get
flutter run
```

By default, the Android emulator uses `http://10.0.2.2:8000` to reach
the backend running on your computer.

For a physical Android device connected to the same Wi-Fi, provide your
computer's local IP address:

``` bash
flutter run --dart-define=API_BASE_URL=http://<your-pc-ip>:8000
```

For local plain-HTTP development, Android needs
`android:usesCleartextTraffic="true"` and the `INTERNET` permission in
`AndroidManifest.xml`.

## API Endpoints

The Flutter app uses these backend endpoints:

  -----------------------------------------------------------------------
  Method                  Endpoint                Purpose
  ----------------------- ----------------------- -----------------------
  `GET`                   `/movies`               Paginated movie
                                                  catalog, search, genre
                                                  filtering, and sorting

  `GET`                   `/movies/genres`        List available genres

  `GET`                   `/movies/{id}`          Movie details

  `POST`                  `/recommendations`      Recommendations from
                                                  five selected movie IDs
  -----------------------------------------------------------------------

Example request body for recommendations:

``` json
{
  "movie_ids": [1, 2, 3, 4, 5],
  "limit": 10
}
```

## Refresh Movie Data from TMDB

To synchronize the backend database with TMDB:

1.  Create an API key at [TMDB API
    settings](https://www.themoviedb.org/settings/api).

2.  Set `TMDB_API_KEY` as an environment variable, or copy
    `.env.example` to `.env` and add the key. **Do not commit your API
    key or `.env` file.**

    **Windows PowerShell (current terminal only):**

    ``` powershell
    $env:TMDB_API_KEY="your_key"
    ```

    **macOS/Linux:**

    ``` bash
    export TMDB_API_KEY=your_key
    ```

3.  Run the first sync:

    ``` bash
    python -m app.sync.sync_movies --pages 10
    ```

4.  For later syncs:

    ``` bash
    python -m app.sync.sync_movies
    ```

5.  Restart the API server so it loads the updated movies.

Useful options include `--dry-run`, `--no-details`,
`--sources top_rated,popular,now_playing,upcoming`, and
`--min-votes 20`.

The sync process fetches data before writing it in a transaction, does
not delete existing movies, and is designed to avoid duplicates. If TMDB
is unavailable or the API key is invalid, the database should remain
unchanged.

The backend's `README.md` contains the detailed synchronization
instructions.

## Tests and Code Checks

**Backend tests** --- from `backend/`:

``` bash
pip install -r requirements-dev.txt
pytest
```

The backend test suite includes `tests/test_golden_api_contract.py`,
which replays 1,159 recorded requests from the original CSV-based API
and checks for identical JSON responses. The tests use a temporary
database rather than your local `movies.db`.

**Flutter checks** --- from `movie_recommender/`:

``` bash
flutter analyze
flutter test
```

## Movie IDs and Database Notes

-   The initial 1,000 movies use IDs `0–999`.
-   New movies receive IDs starting at `1000`; IDs are permanent and are
    not reused.
-   TMDB's ID is stored separately in `tmdb_id`.
-   `data/db.csv` is the starting dataset and a backup. Once
    `data/movies.db` exists, the API uses the SQLite database rather
    than reading the CSV on each start.

## Credits and Disclaimer

This product uses the TMDB API but is not endorsed or certified by TMDB.

## Author

**Tareq Khashaneh**
