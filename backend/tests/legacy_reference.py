import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Load movies dataset
DATA_PATH = "data/db.csv"

movies = pd.read_csv(DATA_PATH)


def recommend_movies(selected_movies, n=5):

    # Remove movies with missing required data
    movies_clean = movies.dropna(
        subset=["Genre", "IMDB_Rating"]
    ).reset_index(drop=True)

    # Convert genres into numerical features
    tfidf = TfidfVectorizer(
        tokenizer=lambda x: x.split(", "),
        token_pattern=None
    )

    genre_matrix = tfidf.fit_transform(
        movies_clean["Genre"]
    )

    # Calculate similarity between movies
    similarity_matrix = cosine_similarity(
        genre_matrix
    )

    # Find selected movie indexes
    movie_indices = movies_clean[
        movies_clean["Series_Title"].isin(selected_movies)
    ].index

    # Check that the movies exist
    if len(movie_indices) == 0:
        return []

    # Calculate average similarity
    similarity_scores = similarity_matrix[
        movie_indices
    ].mean(axis=0)

    # Sort by similarity
    recommended_indices = similarity_scores.argsort()[::-1]

    # Remove movies already selected
    recommended_indices = [
        i for i in recommended_indices
        if i not in movie_indices
    ]

    # Create recommendations dataframe
    recommended_movies = movies_clean.iloc[
        recommended_indices
    ].copy()

    # Add similarity score
    recommended_movies["Similarity"] = (
        similarity_scores[recommended_indices]
    )

    # Normalize IMDb ratings
    rating_range = (
        recommended_movies["IMDB_Rating"].max()
        - recommended_movies["IMDB_Rating"].min()
    )

    if rating_range == 0:
        recommended_movies["Rating_Normalized"] = 0
    else:
        recommended_movies["Rating_Normalized"] = (
            (
                recommended_movies["IMDB_Rating"]
                - recommended_movies["IMDB_Rating"].min()
            )
            / rating_range
        )

    # Calculate final score
    recommended_movies["Final_Score"] = (
        0.7 * recommended_movies["Similarity"]
        + 0.3 * recommended_movies["Rating_Normalized"]
    )

    # Sort by final score
    recommended_movies = recommended_movies.sort_values(
        "Final_Score",
        ascending=False
    )
    # Return top N recommendations
    return recommended_movies[
           [
        "Series_Title",
        "Poster_Link",
        "Released_Year",
        "Genre",
        "IMDB_Rating",
        "Runtime",
        "Overview",
        "Similarity",
        "Final_Score"
    ]
    ].head(n)