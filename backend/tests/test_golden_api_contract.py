"""The API contract must not change when the data source moves from CSV to SQLite.

tests/golden/api_snapshot.json.gz holds the responses of 1159 requests recorded
from the ORIGINAL db.csv-based backend (every /movies page and sort order,
searches, filters, all 1000 movie details, 40+ recommendation sets, the legacy
/recommend endpoint and all error responses). The current backend must return
identical JSON for every one of them.
"""
import gzip
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from tests.golden_api import collect

SNAPSHOT = Path(__file__).parent / "golden" / "api_snapshot.json.gz"


def test_every_response_is_identical_to_the_original_csv_backend():
    with gzip.open(SNAPSHOT, "rt", encoding="utf-8") as f:
        expected = json.load(f)

    actual = collect(TestClient(app))

    assert actual.keys() == expected.keys()
    changed = [key for key in expected if actual[key] != expected[key]]
    assert not changed, f"{len(changed)} of {len(expected)} responses changed; first: {changed[0]}"
