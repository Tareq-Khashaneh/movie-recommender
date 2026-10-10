import random

import pytest
from fastapi.testclient import TestClient

from app import catalog
from app.main import app
from app.reommender import recommend_movies
from tests.legacy_reference import recommend_movies as legacy_recommend_movies

client = TestClient(app)


# ---------- catalog: listing, pagination ----------
def test_list_defaults():
    body = client.get("/movies").json()
    assert body["page"] == 1 and body["page_size"] == 20
    assert body["total"] == 1000 and body["total_pages"] == 50
    assert body["has_next"] is True and body["has_previous"] is False
    assert len(body["items"]) == 20
    ratings = [m["imdb_rating"] for m in body["items"]]
    assert ratings == sorted(ratings, reverse=True)


def test_paging_through_everything_has_no_gaps_or_duplicates():
    seen, page = [], 1
    while True:
        body = client.get("/movies", params={"page": page, "page_size": 50}).json()
        seen += [m["id"] for m in body["items"]]
        if not body["has_next"]:
            break
        page += 1
    assert len(seen) == 1000 and len(set(seen)) == 1000


def test_page_beyond_range_is_empty_not_error():
    body = client.get("/movies", params={"page": 999}).json()
    assert body["items"] == [] and body["has_next"] is False and body["total"] == 1000


# ---------- catalog: search / filter / sort ----------
def test_search_is_case_insensitive_and_covers_director():
    a = client.get("/movies", params={"search": "NOLAN", "page_size": 50}).json()
    b = client.get("/movies", params={"search": "nolan", "page_size": 50}).json()
    assert a["total"] == b["total"] > 0
    for item in a["items"]:
        assert catalog.get_movie(item["id"]).director == "Christopher Nolan"


def test_search_by_title_and_no_match():
    titles = [m["title"] for m in client.get("/movies", params={"search": "godfather"}).json()["items"]]
    assert "The Godfather" in titles
    assert client.get("/movies", params={"search": "zzzzqqq"}).json()["total"] == 0


def test_genre_filter_requires_all_genres():
    body = client.get("/movies", params={"genre": ["drama", "Crime"], "page_size": 50}).json()
    assert body["total"] > 0
    for item in body["items"]:
        assert {"Drama", "Crime"} <= set(item["genres"])


def test_rating_and_year_filters_and_sort():
    body = client.get(
        "/movies",
        params={"min_rating": 8.5, "year_from": 1990, "year_to": 2010, "sort_by": "year", "order": "asc", "page_size": 50},
    ).json()
    assert body["total"] > 0
    years = [m["year"] for m in body["items"]]
    assert years == sorted(years)
    assert all(1990 <= y <= 2010 for y in years)
    assert all(m["imdb_rating"] >= 8.5 for m in body["items"])


def test_sort_by_title():
    titles = [m["title"].lower() for m in client.get("/movies", params={"sort_by": "title", "order": "asc"}).json()["items"]]
    assert titles == sorted(titles)


def test_genres_endpoint():
    genres = client.get("/movies/genres").json()
    assert "Drama" in genres and genres == sorted(genres) and len(genres) == 21


# ---------- details ----------
def test_every_movie_detail_is_valid_json():
    for movie_id in range(1000):
        r = client.get(f"/movies/{movie_id}")
        assert r.status_code == 200
        assert r.json()["id"] == movie_id


def test_apollo_13_data_fix():
    body = client.get("/movies/966").json()
    assert body["title"] == "Apollo 13" and body["year"] == 1995 and body["certificate"] == "PG"


def test_detail_not_found():
    r = client.get("/movies/99999")
    assert r.status_code == 404
    assert r.json() == {"error": {"code": "not_found", "message": "Movie not found"}}


# ---------- error shape ----------
@pytest.mark.parametrize(
    "params",
    [{"page_size": 500}, {"page": 0}, {"sort_by": "bogus"}, {"min_rating": 11}, {"year_from": 2010, "year_to": 2000}],
)
def test_invalid_list_params_return_422_with_standard_shape(params):
    r = client.get("/movies", params=params)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


# ---------- recommendations (new, id-based) ----------
FIVE = [1, 2, 8, 20, 30]


def test_recommendations_happy_path():
    r = client.post("/recommendations", json={"movie_ids": FIVE})
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 10
    ids = [m["id"] for m in items]
    assert not set(ids) & set(FIVE) and len(set(ids)) == len(ids)
    scores = [m["score"] for m in items]
    assert scores == sorted(scores, reverse=True)
    assert {"id", "title", "poster_url", "year", "genres", "imdb_rating", "similarity", "score"} <= set(items[0])


def test_recommendations_limit():
    assert len(client.post("/recommendations", json={"movie_ids": FIVE, "limit": 3}).json()["items"]) == 3


@pytest.mark.parametrize(
    "body",
    [{"movie_ids": []}, {"movie_ids": list(range(11))}, {"movie_ids": [1, 1]}, {"movie_ids": [1], "limit": 0}, {"movie_ids": ["a"]}, {}],
)
def test_recommendations_validation(body):
    r = client.post("/recommendations", json=body)
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


def test_recommendations_unknown_id():
    r = client.post("/recommendations", json={"movie_ids": [1, 99999]})
    assert r.status_code == 422 and "99999" in r.json()["error"]["message"]


def test_duplicate_title_is_resolved_by_id():
    # Drishyam (2013) is id 87 and Drishyam (2015) is id 136: selecting one
    # must not hide the other, but must exclude itself.
    ids = [m["id"] for m in client.post("/recommendations", json={"movie_ids": [87], "limit": 20}).json()["items"]]
    assert 87 not in ids


# ---------- recommender: algorithm unchanged ----------
def test_refactored_recommender_matches_original_algorithm():
    rng = random.Random(42)
    titles = list(catalog._movies["title"].unique())
    for _ in range(40):
        picks = rng.sample(titles, 5)
        old = legacy_recommend_movies(picks)
        new = recommend_movies(picks)
        assert list(old["Series_Title"]) == list(new["Series_Title"])
        assert list(old["Final_Score"]) == pytest.approx(list(new["Final_Score"]))


# ---------- legacy endpoint ----------
def test_legacy_recommend_endpoint_still_works():
    ok = client.post("/recommend", json=["The Godfather", "Fight Club"])
    assert ok.status_code == 200 and len(ok.json()["recommendations"]) == 5
    assert client.post("/recommend", json=["No Such Movie"]).json() == {"recommendations": []}


def test_health_and_root():
    assert client.get("/health").json() == {"status": "ok", "movies": 1000}
    assert client.get("/").status_code == 200
