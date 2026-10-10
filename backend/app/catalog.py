"""In-memory movie catalog built from the SQLite movie database.

The movies are loaded and cleaned once at startup (restart the server after a
TMDB sync to pick up new movies) and filtered with pandas. This keeps the API
fast and dependency-free. If the data ever grows to 100k+ rows, swap this
module for SQL queries; the router and schemas do not need to change.
"""
import math

import pandas as pd

from app.database.movie_store import load_movies_frame
from app.schemas import MovieDetail, MovieSummary, SortBy, SortOrder

_SORT_COLUMNS = {
    SortBy.rating: "imdb_rating",
    SortBy.year: "year",
    SortBy.title: "title_sort",
    SortBy.votes: "votes",
}


def _load() -> pd.DataFrame:
    raw = load_movies_frame()  # db.csv-shaped frame, indexed by the API-facing movie id

    df = pd.DataFrame(
        {
            "id": raw.index.astype(int),  # API-facing id; never reused, never changes
            "title": raw["Series_Title"],
            "poster_url": raw["Poster_Link"],
            # Non-numeric values (e.g. "PG" in the Apollo 13 row) become NaN -> None
            "year": pd.to_numeric(raw["Released_Year"], errors="coerce"),
            "certificate": raw["Certificate"],
            "runtime_minutes": pd.to_numeric(
                raw["Runtime"].str.extract(r"(\d+)")[0], errors="coerce"
            ),
            "genres": raw["Genre"].fillna("").map(
                lambda g: [x.strip() for x in g.split(",") if x.strip()]
            ),
            "imdb_rating": raw["IMDB_Rating"],
            "overview": raw["Overview"],
            "meta_score": raw["Meta_score"],
            "director": raw["Director"],
            "cast": raw[["Star1", "Star2", "Star3", "Star4"]].apply(
                lambda row: [s for s in row if isinstance(s, str) and s], axis=1
            ),
            "votes": raw["No_of_Votes"],
            "gross": pd.to_numeric(
                raw["Gross"].str.replace(",", "", regex=False), errors="coerce"
            ),
        }
    )

    df["title_sort"] = df["title"].str.lower()
    # Precomputed lowercase blob so search is a single vectorised substring check
    df["search_blob"] = (
        df["title"].fillna("")
        + " | "
        + df["director"].fillna("")
        + " | "
        + df["cast"].map(" ".join)
    ).str.lower()
    df["genres_lower"] = df["genres"].map(lambda gs: {g.lower() for g in gs})
    return df


_movies = _load()

ALL_GENRES: list[str] = sorted({g for gs in _movies["genres"] for g in gs})


def _clean(value):
    """NaN -> None so the response is valid JSON."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return value


def _int_or_none(value):
    value = _clean(value)
    return None if value is None else int(value)


def _summary(row) -> MovieSummary:
    return MovieSummary(
        id=int(row["id"]),
        title=row["title"],
        poster_url=_clean(row["poster_url"]),
        year=_int_or_none(row["year"]),
        genres=row["genres"],
        imdb_rating=float(row["imdb_rating"]),
    )


def _detail(row) -> MovieDetail:
    return MovieDetail(
        **_summary(row).model_dump(),
        certificate=_clean(row["certificate"]),
        runtime_minutes=_int_or_none(row["runtime_minutes"]),
        overview=_clean(row["overview"]),
        meta_score=_int_or_none(row["meta_score"]),
        director=_clean(row["director"]),
        cast=row["cast"],
        votes=_int_or_none(row["votes"]),
        gross=_int_or_none(row["gross"]),
    )


def query_movies(
    *,
    page: int,
    page_size: int,
    search: str | None,
    genres: list[str],
    min_rating: float | None,
    year_from: int | None,
    year_to: int | None,
    sort_by: SortBy,
    order: SortOrder,
) -> tuple[list[MovieSummary], int]:
    """Return (page_items, total_matching)."""
    df = _movies
    mask = pd.Series(True, index=df.index)

    if search:
        mask &= df["search_blob"].str.contains(
            search.strip().lower(), regex=False, na=False
        )

    for genre in genres:  # AND semantics: movie must have every requested genre
        wanted = genre.strip().lower()
        mask &= df["genres_lower"].map(lambda gs, w=wanted: w in gs)

    if min_rating is not None:
        mask &= df["imdb_rating"] >= min_rating
    if year_from is not None:
        mask &= df["year"] >= year_from
    if year_to is not None:
        mask &= df["year"] <= year_to

    filtered = df[mask]
    total = len(filtered)

    # "id" as the tie-breaker keeps pagination stable between requests
    filtered = filtered.sort_values(
        [_SORT_COLUMNS[sort_by], "id"],
        ascending=[order == SortOrder.asc, True],
        na_position="last",
    )

    start = (page - 1) * page_size
    window = filtered.iloc[start : start + page_size]
    return [_summary(row) for _, row in window.iterrows()], total


def get_movie(movie_id: int) -> MovieDetail | None:
    if movie_id not in _movies.index:
        return None
    return _detail(_movies.loc[movie_id])


def get_summary(movie_id: int) -> MovieSummary | None:
    if movie_id not in _movies.index:
        return None
    return _summary(_movies.loc[movie_id])


def movie_count() -> int:
    return len(_movies)
