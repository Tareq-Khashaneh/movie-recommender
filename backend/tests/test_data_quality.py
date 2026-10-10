import pandas as pd

from app.reommender import DATA_PATH

REQUIRED = ["Series_Title", "Poster_Link", "Released_Year", "Genre", "IMDB_Rating", "Overview", "Runtime"]


def test_required_columns_have_no_nulls():
    df = pd.read_csv(DATA_PATH)
    for col in REQUIRED:
        assert col in df.columns, f"missing column {col}"
        assert df[col].isna().sum() == 0, f"nulls in {col}"


def test_years_and_ratings_are_valid():
    df = pd.read_csv(DATA_PATH)
    assert df["Released_Year"].astype(str).str.fullmatch(r"\d{4}").all()
    assert df["IMDB_Rating"].between(0, 10).all()


def test_optional_columns_may_be_null_but_api_handles_it():
    # Certificate / Meta_score / Gross legitimately contain nulls in this dataset
    df = pd.read_csv(DATA_PATH)
    assert df[["Certificate", "Meta_score", "Gross"]].isna().any().any()
