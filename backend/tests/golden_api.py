"""A fixed battery of API requests used to prove the API contract never changes.

`collect(client)` returns {request-description: {"status": ..., "body": ...}}.
tests/golden/api_snapshot.json.gz was recorded from the ORIGINAL CSV-based
backend; test_golden_api_contract.py replays the same requests against the
current backend and requires byte-for-byte identical JSON.
"""
import random


def collect(client) -> dict:
    out: dict = {}

    def record(key: str, response) -> None:
        try:
            body = response.json()
        except ValueError:
            body = response.text
        out[key] = {"status": response.status_code, "body": body}

    def get(path: str, **params) -> None:
        record(f"GET {path} {sorted(params.items())}", client.get(path, params=params))

    def post(path: str, payload) -> None:
        record(f"POST {path} {payload}", client.post(path, json=payload))

    # --- basics
    get("/")
    get("/health")
    get("/movies/genres")

    # --- catalog: every page of the default listing, plus all sort combinations
    for page in range(1, 22):
        get("/movies", page=page, page_size=50)
    for page in (1, 2, 3):
        get("/movies", page=page, page_size=20)
    for sort_by in ("rating", "year", "title", "votes"):
        for order in ("asc", "desc"):
            get("/movies", sort_by=sort_by, order=order, page_size=50)
            get("/movies", sort_by=sort_by, order=order, page=2, page_size=17)

    # --- search / filters
    for term in ("nolan", "dicaprio", "godfather", "THE", "zzzzzz", "kubrick", "spielberg", "love"):
        get("/movies", search=term, page_size=50)
    for genres in (["Drama"], ["Drama", "Crime"], ["Sci-Fi"], ["Action", "Adventure", "Sci-Fi"],
                   ["Western"], ["Film-Noir"], ["nonexistent"]):
        get("/movies", genre=genres, page_size=50)
    get("/movies", min_rating=8.5, page_size=50)
    get("/movies", min_rating=9, page_size=50)
    get("/movies", year_from=1990, year_to=2010, page_size=50)
    get("/movies", year_from=2015, page_size=50)
    get("/movies", year_to=1950, page_size=50)
    get("/movies", search="the", genre="Action", min_rating=8, sort_by="year", order="asc", page_size=50)

    # --- validation errors
    for params in ({"page": 0}, {"page_size": 0}, {"page_size": 51}, {"min_rating": 11},
                   {"sort_by": "bogus"}, {"year_from": 2010, "year_to": 2000}, {"order": "sideways"}):
        get("/movies", **params)
    get("/movies", page=999)

    # --- every movie detail (ids 0..999) plus bad ids
    for movie_id in range(1000):
        get(f"/movies/{movie_id}")
    for bad in ("1000", "-1", "abc", "99999"):
        get(f"/movies/{bad}")

    # --- recommendations by id
    rng = random.Random(7)
    for _ in range(40):
        post("/recommendations", {"movie_ids": rng.sample(range(1000), 5), "limit": 10})
    for size in (1, 2, 3, 4):
        post("/recommendations", {"movie_ids": rng.sample(range(1000), size)})
    for limit in (1, 3, 20, 50):
        post("/recommendations", {"movie_ids": [1, 2, 8, 20, 30], "limit": limit})
    post("/recommendations", {"movie_ids": [87, 136, 500]})  # includes both "Drishyam" rows
    post("/recommendations", {"movie_ids": []})
    post("/recommendations", {"movie_ids": [1, 2, 3, 4, 5, 6]})
    post("/recommendations", {"movie_ids": [1, 99999]})
    post("/recommendations", {"movie_ids": [1, 2], "limit": 0})
    post("/recommendations", {"bogus": True})

    # --- legacy title-based endpoint
    titles = [m["title"] for m in client.get("/movies", params={"page_size": 50}).json()["items"]]
    for _ in range(25):
        post("/recommend", rng.sample(titles, 5))
    post("/recommend", ["Definitely Not A Movie"])
    post("/recommend", [titles[0]])
    post("/recommend", ["Drishyam"])
    post("/recommend", [])
    return out
