"""Content-based recommender: genre TF-IDF + cosine similarity + IMDb rating.

The scoring math is unchanged from the original implementation. Two things
changed for the API:
  * the TF-IDF / similarity matrix is computed once at import time instead of
    on every request (same result, much less work per call);
  * selections can be made by movie_id (the API-facing movie id) as well as by title,
    which resolves duplicate titles such as "Drishyam" (2013 vs 2015).
"""
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.database.movie_store import load_movies_frame

# The runtime data source is now SQLite (see app/database). db.csv is only the
# one-time import source / backup.
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "db.csv"

# Same columns/formats as db.csv, indexed by the API-facing movie id.
movies = load_movies_frame()

# Remove movies with missing required data. "movie_id" is the API-facing id
# (the frame's index) so results can be matched with the catalog after re-indexing.
movies_clean = (
    movies.dropna(subset=["Genre", "IMDB_Rating"])
    .rename_axis("movie_id")
    .reset_index()
)

# Convert genres into numerical features and calculate similarity between movies
_tfidf = TfidfVectorizer(tokenizer=lambda x: x.split(", "), token_pattern=None)
_genre_matrix = _tfidf.fit_transform(movies_clean["Genre"])
similarity_matrix = cosine_similarity(_genre_matrix)

# Columns returned by the legacy title-based function (kept for compatibility)
_LEGACY_COLUMNS = [
    "Series_Title",
    "Poster_Link",
    "Released_Year",
    "Genre",
    "IMDB_Rating",
    "Runtime",
    "Overview",
    "Similarity",
    "Final_Score",
]


def _rank(movie_indices: pd.Index) -> pd.DataFrame:
    """Rank every non-selected movie against the selected rows."""
    # Calculate average similarity
    similarity_scores = similarity_matrix[movie_indices].mean(axis=0)

    # Sort by similarity
    recommended_indices = similarity_scores.argsort()[::-1]

    # Remove movies already selected
    recommended_indices = [i for i in recommended_indices if i not in movie_indices]

    recommended_movies = movies_clean.iloc[recommended_indices].copy()
    recommended_movies["Similarity"] = similarity_scores[recommended_indices]

    # Normalize IMDb ratings
    rating_range = (
        recommended_movies["IMDB_Rating"].max()
        - recommended_movies["IMDB_Rating"].min()
    )
    if rating_range == 0:
        recommended_movies["Rating_Normalized"] = 0
    else:
        recommended_movies["Rating_Normalized"] = (
            recommended_movies["IMDB_Rating"] - recommended_movies["IMDB_Rating"].min()
        ) / rating_range

    # Calculate final score and sort by it
    recommended_movies["Final_Score"] = (
        0.7 * recommended_movies["Similarity"]
        + 0.3 * recommended_movies["Rating_Normalized"]
    )
    return recommended_movies.sort_values("Final_Score", ascending=False)


def recommend_movies(selected_movies, n=5):
    """Legacy: recommend by exact titles. Returns [] if no title matches."""
    movie_indices = movies_clean[
        movies_clean["Series_Title"].isin(selected_movies)
    ].index
    if len(movie_indices) == 0:
        return []
    return _rank(movie_indices)[_LEGACY_COLUMNS].head(n)


def recommend_by_ids(movie_ids, n=10):
    """Recommend by movie_id. Returns [] if none of the ids are usable."""
    movie_indices = movies_clean.index[movies_clean["movie_id"].isin(movie_ids)]
    if len(movie_indices) == 0:
        return []
    return _rank(movie_indices).head(n)
