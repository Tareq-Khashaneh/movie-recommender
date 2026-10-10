import math

from fastapi import APIRouter, HTTPException, Query

from app import catalog
from app.schemas import MovieDetail, MovieSummary, Page, SortBy, SortOrder

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("", response_model=Page[MovieSummary])
def list_movies(
    page: int = Query(1, ge=1, description="1-based page number"),
    page_size: int = Query(20, ge=1, le=50),
    search: str | None = Query(
        None, min_length=1, max_length=100,
        description="Case-insensitive match on title, director or cast",
    ),
    genre: list[str] = Query(
        default=[], description="Repeat to require several genres, e.g. ?genre=Drama&genre=Crime"
    ),
    min_rating: float | None = Query(None, ge=0, le=10),
    year_from: int | None = Query(None, ge=1880, le=2100),
    year_to: int | None = Query(None, ge=1880, le=2100),
    sort_by: SortBy = SortBy.rating,
    order: SortOrder = SortOrder.desc,
):
    if year_from is not None and year_to is not None and year_from > year_to:
        raise HTTPException(status_code=422, detail="year_from must be <= year_to")

    items, total = catalog.query_movies(
        page=page,
        page_size=page_size,
        search=search,
        genres=genre,
        min_rating=min_rating,
        year_from=year_from,
        year_to=year_to,
        sort_by=sort_by,
        order=order,
    )
    total_pages = math.ceil(total / page_size)
    return Page[MovieSummary](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


# Declared before "/{movie_id}" so "genres" is never parsed as an id.
@router.get("/genres", response_model=list[str])
def list_genres():
    return catalog.ALL_GENRES


@router.get("/{movie_id}", response_model=MovieDetail)
def get_movie(movie_id: int):
    movie = catalog.get_movie(movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie
