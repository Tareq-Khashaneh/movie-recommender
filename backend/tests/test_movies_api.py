import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get(path, **params):
    return client.get(path, params=params)


def test_root():
    assert get("/").json() == {"message": "Movie Recommendation API is running"}


def test_pagination_walks_every_movie_exactly_once():
    seen, page = [], 1
    while True:
        body = get("/movies", page=page, page_size=50).json()
        seen += [m["id"] for m in body["items"]]
        assert body["total"] == 1000
        if not body["has_next"]:
            break
        page += 1
    assert len(seen) == 1000 and len(set(seen)) == 1000
    assert page == 20


def test_page_beyond_end_is_empty_not_error():
    r = get("/movies", page=999)
    assert r.status_code == 200
    assert r.json()["items"] == [] and r.json()["has_next"] is False


def test_default_sort_is_rating_desc():
    ratings = [m["imdb_rating"] for m in get("/movies", page_size=50).json()["items"]]
    assert ratings == sorted(ratings, reverse=True)


@pytest.mark.parametrize("sort_by", ["rating", "year", "title", "votes"])
@pytest.mark.parametrize("order", ["asc", "desc"])
def test_all_sort_combinations_work(sort_by, order):
    assert get("/movies", sort_by=sort_by, order=order).status_code == 200


def test_search_by_title_director_and_cast_is_case_insensitive():
    assert any(m["title"] == "Inception" for m in get("/movies", search="INCEPT").json()["items"])
    assert get("/movies", search="christopher nolan").json()["total"] > 0
    assert get("/movies", search="leonardo dicaprio").json()["total"] > 0
    assert get("/movies", search="zzzzzz").json()["total"] == 0


def test_genre_filter_requires_all_genres():
    both = get("/movies", genre=["Drama", "Crime"], page_size=50).json()
    assert both["total"] > 0
    assert all({"Drama", "Crime"} <= set(m["genres"]) for m in both["items"])
    assert both["total"] < get("/movies", genre="Drama").json()["total"]


def test_rating_and_year_filters():
    body = get("/movies", min_rating=8.5, year_from=1990, year_to=2010, page_size=50).json()
    assert body["total"] > 0
    assert all(m["imdb_rating"] >= 8.5 and 1990 <= m["year"] <= 2010 for m in body["items"])


def test_combined_filters_and_search():
    body = get("/movies", search="the", genre="Action", min_rating=8, sort_by="year", order="asc").json()
    years = [m["year"] for m in body["items"]]
    assert years == sorted(years)


@pytest.mark.parametrize(
    "params",
    [{"page": 0}, {"page_size": 0}, {"page_size": 51}, {"min_rating": 11},
     {"sort_by": "bogus"}, {"year_from": 2010, "year_to": 2000}],
)
def test_invalid_params_return_422(params):
    assert get("/movies", **params).status_code == 422


def test_genres_endpoint():
    genres = get("/movies/genres").json()
    assert len(genres) == 21 and "Drama" in genres and genres == sorted(genres)


def test_every_movie_detail_is_valid_json_without_nan():
    for movie_id in range(1000):
        r = get(f"/movies/{movie_id}")
        assert r.status_code == 200, movie_id
        assert "NaN" not in r.text, movie_id
    assert get("/movies/966").json()["year"] == 1995  # Apollo 13 fixed


def test_detail_not_found_and_bad_id():
    assert get("/movies/1000").status_code == 404
    assert get("/movies/-1").status_code == 404
    assert get("/movies/abc").status_code == 422


def test_list_has_no_nan_anywhere():
    for page in range(1, 21):
        assert "NaN" not in get("/movies", page=page, page_size=50).text
