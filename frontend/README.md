# Movie Recommender (Flutter)

A content-based movie recommendation app. Pick 5 movies you like, get 10 similar ones.
The Flutter client talks to a FastAPI backend (TF-IDF on genres + cosine similarity over the IMDb top-1000).

## Features
- Browse the catalog with **infinite scroll**, **debounced search** (title / director / cast), **genre filters** and **sorting**
- Select exactly 5 movies with a live "3 / 5" counter and removable thumbnails
- Recommendation grid with a match badge, and a details screen (overview, runtime, cast, votes, box office...)
- Loading, empty and error states everywhere, with retry; timeouts, offline and invalid-response handling

## Architecture
Feature-first Clean Architecture with Riverpod 3 and Dio.

```
lib/
  core/            constants (API url), network (Dio, Failure types), theme, utils
  features/movies/
    domain/        entities, repository interface        (pure Dart)
    data/          models (JSON), remote data source, repository implementation
    presentation/  providers (Riverpod), screens, widgets
```

Data flow: `Widget -> Provider -> MoviesRepository -> RemoteDataSource -> Dio -> FastAPI`.
Errors are converted once (in the repository) into typed `Failure`s that the UI displays.

## Backend endpoints used
| Method | Path | Purpose |
|---|---|---|
| GET | `/movies` | paginated catalog: `page, page_size, search, genre, sort_by, order` |
| GET | `/movies/genres` | genre chips |
| GET | `/movies/{id}` | details screen |
| POST | `/recommendations` | `{"movie_ids": [..5 ids..], "limit": 10}` |

## Run
```bash
flutter pub get
# emulator (default http://10.0.2.2:8000)
flutter run
# physical device on the same Wi-Fi
flutter run --dart-define=API_BASE_URL=http://<your-pc-ip>:8000
```
Android needs `android:usesCleartextTraffic="true"` (plain-http dev backend) and the
`INTERNET` permission in `AndroidManifest.xml`.

## Test
```bash
flutter analyze
flutter test
```
