"""TMDB API client + the mapping layer from TMDB's JSON to our database format.

Uses only the standard library (urllib), so there are no new dependencies.
The API key is read from the TMDB_API_KEY environment variable (or a local
.env file) and is never hard-coded.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from app.database.connection import PROJECT_ROOT
from app.database.movie_store import MovieRecord

API_BASE = os.environ.get("TMDB_API_BASE", "https://api.themoviedb.org/3")
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

SOURCES = ("top_rated", "popular", "now_playing", "upcoming")

# TMDB genre name -> the name already used by the app's genre filter (from db.csv)
GENRE_ALIASES = {"Science Fiction": "Sci-Fi"}


class TMDBError(Exception):
    """Base class for every TMDB problem."""


class MissingApiKeyError(TMDBError):
    pass


class TMDBAuthError(TMDBError):
    """TMDB rejected the API key (HTTP 401/403)."""


class TMDBNotFoundError(TMDBError):
    """HTTP 404 for one movie."""


class TMDBRequestError(TMDBError):
    """Request still failing after all retries."""


# ----------------------------------------------------------------------------- API key
def load_env_file(path=PROJECT_ROOT / ".env") -> None:
    """Minimal .env reader (KEY=VALUE lines). Real environment variables win."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_api_key() -> str:
    load_env_file()
    key = os.environ.get("TMDB_API_KEY", "").strip()
    if not key:
        raise MissingApiKeyError(
            "TMDB_API_KEY is not set. Create a free key at https://www.themoviedb.org/settings/api "
            "and set it as an environment variable (or put TMDB_API_KEY=... in a .env file "
            "next to the data/ folder)."
        )
    return key


# ---------------------------------------------------------------------------- HTTP
def _urllib_fetch(url: str, headers: dict, timeout: float):
    """Returns (status, headers, body). Network errors are raised."""
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:  # 4xx/5xx still carry a status code
        return error.code, dict(error.headers or {}), error.read()


class TMDBClient:
    def __init__(self, api_key: str, *, fetch=_urllib_fetch, sleep=time.sleep,
                 max_retries: int = 3, timeout: float = 15.0, base_url: str | None = None):
        self._api_key = api_key
        self._fetch = fetch
        self._sleep = sleep
        self._max_retries = max_retries
        self._timeout = timeout
        self._base_url = (base_url or API_BASE).rstrip("/")

    def _get_json(self, path: str, params: dict | None = None) -> dict:
        params = dict(params or {})
        headers = {"Accept": "application/json"}
        if self._api_key.startswith("eyJ"):  # v4 "API Read Access Token" (a JWT)
            headers["Authorization"] = f"Bearer {self._api_key}"
        else:  # classic v3 API key
            params["api_key"] = self._api_key
        url = f"{self._base_url}{path}?{urllib.parse.urlencode(params)}"

        last_problem = "unknown error"
        for attempt in range(self._max_retries + 1):
            delay = 2.0**attempt
            try:
                status, response_headers, body = self._fetch(url, headers, self._timeout)
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                last_problem = f"network error: {error}"
            else:
                if status == 200:
                    try:
                        return json.loads(body)
                    except ValueError as error:
                        raise TMDBRequestError(f"TMDB sent invalid JSON for {path}") from error
                if status in (401, 403):
                    raise TMDBAuthError(
                        "TMDB rejected the API key (HTTP %d). Check TMDB_API_KEY." % status
                    )
                if status == 404:
                    raise TMDBNotFoundError(f"TMDB has no resource {path}")
                if status != 429 and status < 500:
                    raise TMDBRequestError(f"TMDB answered HTTP {status} for {path}")
                last_problem = f"HTTP {status}"
                retry_after = {k.lower(): v for k, v in response_headers.items()}.get("retry-after")
                if retry_after and retry_after.isdigit():
                    delay = float(retry_after)
            if attempt < self._max_retries:
                self._sleep(delay)
        raise TMDBRequestError(
            f"TMDB request {path} failed after {self._max_retries + 1} attempts ({last_problem})"
        )

    # ------------------------------------------------------------------- endpoints
    def genre_map(self) -> dict[int, str]:
        data = self._get_json("/genre/movie/list", {"language": "en-US"})
        return {g["id"]: g["name"] for g in data.get("genres", [])}

    def list_movies(self, source: str, page: int) -> tuple[list[dict], int]:
        """One page of a TMDB movie list. Returns (results, total_pages)."""
        data = self._get_json(f"/movie/{source}", {"language": "en-US", "page": page})
        return data.get("results", []), int(data.get("total_pages", 1))

    def movie_details(self, tmdb_id: int) -> dict:
        return self._get_json(
            f"/movie/{tmdb_id}", {"language": "en-US", "append_to_response": "credits"}
        )


# ------------------------------------------------------------- mapping layer (TMDB -> ours)
def _genre_names(item: dict, details: dict | None, genre_map: dict[int, str]) -> str:
    if details and details.get("genres"):
        names = [g["name"] for g in details["genres"]]
    else:
        names = [genre_map[i] for i in item.get("genre_ids", []) if i in genre_map]
    return ", ".join(GENRE_ALIASES.get(name, name) for name in names)


def normalize_movie(item: dict, details: dict | None, genre_map: dict[int, str]) -> MovieRecord | None:
    """Turn a TMDB list item (+ optional details) into a MovieRecord.

    Returns None when the movie lacks what the app needs (release year, genres,
    title) or is adult content.
    """
    merged = {**item, **(details or {})}
    release_date = (merged.get("release_date") or "").strip()
    title = (merged.get("title") or "").strip()
    genres = _genre_names(item, details, genre_map)
    if merged.get("adult") or not title or len(release_date) < 4 or not release_date[:4].isdigit() or not genres:
        return None

    credits = (details or {}).get("credits") or {}
    cast = [p["name"] for p in sorted(credits.get("cast", []), key=lambda p: p.get("order", 999))
            if p.get("name")][:4]
    director = next((p["name"] for p in credits.get("crew", []) if p.get("job") == "Director"), None)

    poster_path = merged.get("poster_path") or None
    return MovieRecord(
        tmdb_id=int(merged["id"]),
        title=title,
        release_year=int(release_date[:4]),
        release_date=release_date if len(release_date) == 10 else None,
        rating=round(float(merged.get("vote_average") or 0), 1),
        vote_count=int(merged.get("vote_count") or 0),
        genres=genres,
        overview=(merged.get("overview") or "").strip() or None,
        runtime_minutes=int(merged["runtime"]) if merged.get("runtime") else None,
        poster_path=poster_path,
        poster_url=f"{IMAGE_BASE}{poster_path}" if poster_path else None,
        backdrop_path=merged.get("backdrop_path") or None,
        director=director,
        cast_names=cast,
        gross=int(merged["revenue"]) if merged.get("revenue") else None,
    )
