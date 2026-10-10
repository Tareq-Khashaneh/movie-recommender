"""One-time migration: data/db.csv -> SQLite.

    python -m app.database.migrate_csv

Safe to run again: it only imports into an EMPTY database and never deletes
or overwrites anything. (Starting the API does the same import automatically
the first time, so running this by hand is optional.)
"""
import sys

from app.database.connection import CSV_PATH, connect, get_db_path
from app.database.movie_store import count_movies, import_csv


def main() -> int:
    conn = connect()
    try:
        existing = count_movies(conn)
        if existing:
            print(f"{get_db_path()} already has {existing} movies - nothing to do.")
            return 0
        if not CSV_PATH.exists():
            print(f"Cannot import: {CSV_PATH} not found.")
            return 1
        imported = import_csv(conn)
        print(f"Imported {imported} movies from {CSV_PATH.name} into {get_db_path()}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
