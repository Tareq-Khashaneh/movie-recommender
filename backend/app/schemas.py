from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


class SortBy(str, Enum):
    rating = "rating"
    year = "year"
    title = "title"
    votes = "votes"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class MovieSummary(BaseModel):
    """Lightweight shape for lists/grids (cards)."""

    id: int
    title: str
    poster_url: str | None
    year: int | None
    genres: list[str]
    imdb_rating: float


class MovieDetail(MovieSummary):
    """Full shape for the details screen."""

    certificate: str | None
    runtime_minutes: int | None
    overview: str | None
    meta_score: int | None
    director: str | None
    cast: list[str]
    votes: int | None
    gross: int | None


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool


class RecommendationRequest(BaseModel):
    movie_ids: list[int] = Field(
        min_length=1, max_length=10, description="Ids of the movies the user liked"
    )
    limit: int = Field(10, ge=1, le=20, description="How many recommendations to return")

    @field_validator("movie_ids")
    @classmethod
    def ids_must_be_unique(cls, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise ValueError("movie_ids must be unique")
        return value


class RecommendedMovie(MovieSummary):
    similarity: float  # genre similarity to the selection, 0..1
    score: float  # final ranking score (70% similarity + 30% normalised rating)


class RecommendationResponse(BaseModel):
    items: list[RecommendedMovie]
