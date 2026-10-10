"""Fill / refresh the SQLite movie database from TMDB.

    python -m app.sync.sync_movies                 # normal sync
    python -m app.sync.sync_movies --pages 10      # go deeper (first run)
    python -m app.sync.sync_movies --dry-run       # fetch and report, write nothing

Safety rules:
* Everything is fetched FIRST; the database is written in a single transaction
  afterwards, so a failure can never leave it half-updated.
* Movies are never deleted. If TMDB is down or the key is wrong, the database
  stays exactly as it was and the command exits with an error.
* Running it twice does not create duplicates (movies are matched by TMDB id).
* Restart the API server after a sync to load the new movies.
"""
import argparse
import sys
from dataclasses import dataclass, field

from app.database.connection import connect, get_db_path
from app.database.movie_store import MovieRecord, count_movies, ensure_database, upsert_movies
from app.services.tmdb import (
    SOURCES,
    MissingApiKeyError,
    TMDBAuthError,
    TMDBClient,
    TMDBError,
    TMDBNotFoundError,
    get_api_key,
    normalize_movie,
)

DEFAULT_SOURCES = ("top_rated", "popular", "now_playing")


class SyncError(RuntimeError):
    """The sync could not produce usable data; the database was not changed."""


@dataclass
class SyncReport:
    candidates: int = 0
    skipped: int = 0
    detail_failures: int = 0
    inserted: int = 0
    updated: int = 0
    linked: int = 0
    warnings: list[str] = field(default_factory=list)


def collect_records(client: TMDBClient, *, sources, pages: int, min_votes: int,
                    with_details: bool, report: SyncReport, log=print) -> list[MovieRecord]:
    """Fetch lists (+ per-movie details) from TMDB and normalise them. Writes nothing."""
    genre_map = client.genre_map()

    items: dict[int, dict] = {}
    for source in sources:
        for page in range(1, pages + 1):
            try:
                results, total_pages = client.list_movies(source, page)
            except TMDBAuthError:
                raise
            except TMDBError as error:
                report.warnings.append(f"{source} page {page}: {error}")
                log(f"  warning: {source} page {page} failed, moving on ({error})")
                break
            for item in results:
                items.setdefault(int(item["id"]), item)
            if page >= total_pages:
                break
        log(f"  fetched list '{source}' (total unique movies so far: {len(items)})")

    wanted = [i for i in items.values() if int(i.get("vote_count") or 0) >= min_votes]
    report.skipped += len(items) - len(wanted)
    records: list[MovieRecord] = []
    for number, item in enumerate(wanted, start=1):
        details = None
        if with_details:
            try:
                details = client.movie_details(int(item["id"]))
            except TMDBAuthError:
                raise
            except TMDBNotFoundError:
                report.skipped += 1
                continue
            except TMDBError as error:  # keep the movie, using list data only
                report.detail_failures += 1
                report.warnings.append(f"details for {item['id']}: {error}")
            if number % 25 == 0:
                log(f"  details {number}/{len(wanted)}")
        record = normalize_movie(item, details, genre_map)
        if record is None:
            report.skipped += 1
        else:
            records.append(record)
    report.candidates = len(records)
    return records


def run_sync(client: TMDBClient, conn, *, sources=DEFAULT_SOURCES, pages: int = 5,
             min_votes: int = 20, with_details: bool = True, dry_run: bool = False,
             log=print) -> SyncReport:
    report = SyncReport()
    records = collect_records(client, sources=sources, pages=pages, min_votes=min_votes,
                              with_details=with_details, report=report, log=log)
    if not records:
        raise SyncError("TMDB returned no usable movies; the database was left unchanged.")
    if not dry_run:
        stats = upsert_movies(conn, records)
        report.inserted, report.updated, report.linked = stats.inserted, stats.updated, stats.linked
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Sync the movie database from TMDB.")
    parser.add_argument("--sources", default=",".join(DEFAULT_SOURCES),
                        help=f"comma-separated TMDB lists: {', '.join(SOURCES)}")
    parser.add_argument("--pages", type=int, default=5, help="pages per list (20 movies each)")
    parser.add_argument("--min-votes", type=int, default=20,
                        help="ignore movies with fewer TMDB votes")
    parser.add_argument("--no-details", action="store_true",
                        help="faster: skip per-movie calls (no runtime/director/cast for new movies)")
    parser.add_argument("--dry-run", action="store_true", help="fetch and report only")
    args = parser.parse_args(argv)

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    unknown = [s for s in sources if s not in SOURCES]
    if unknown:
        print(f"Unknown source(s): {', '.join(unknown)}. Choose from: {', '.join(SOURCES)}")
        return 2

    try:
        client = TMDBClient(get_api_key())
    except MissingApiKeyError as error:
        print(f"ERROR: {error}")
        return 2

    # First run: imports db.csv (if present) so its movies are linked, not duplicated.
    # Without db.csv the sync simply fills an empty database from TMDB alone.
    ensure_database(allow_empty=True)
    conn = connect()
    try:
        before = count_movies(conn)
        print(f"Database: {get_db_path()} ({before} movies). Syncing from TMDB...")
        report = run_sync(client, conn, sources=sources, pages=args.pages,
                          min_votes=args.min_votes, with_details=not args.no_details,
                          dry_run=args.dry_run)
        after = count_movies(conn)
    except TMDBAuthError as error:
        print(f"ERROR: {error} The database was not changed.")
        return 1
    except (SyncError, TMDBError) as error:
        print(f"ERROR: {error}")
        return 1
    finally:
        conn.close()

    print(f"Done{' (dry run, nothing written)' if args.dry_run else ''}: "
          f"{report.candidates} usable movies from TMDB "
          f"({report.skipped} skipped, {report.detail_failures} detail lookups failed).")
    if not args.dry_run:
        print(f"  inserted {report.inserted}, updated {report.updated}, "
              f"linked to existing {report.linked}. Database now has {after} movies.")
        print("  Restart the API server to load the new movies.")
    for warning in report.warnings[:10]:
        print(f"  warning: {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
