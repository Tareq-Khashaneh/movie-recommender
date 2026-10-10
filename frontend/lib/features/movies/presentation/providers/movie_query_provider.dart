import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/entities/movie_query.dart';

/// The search text, genre filters and sort order the user has chosen.
/// The catalog provider watches this and reloads when it changes.
class MovieQueryNotifier extends Notifier<MovieQuery> {
  @override
  MovieQuery build() => const MovieQuery();

  void setSearch(String value) {
    final search = value.trim();
    if (search == state.search) return;
    state = state.copyWith(search: search);
  }

  void toggleGenre(String genre) {
    final genres = state.genres.contains(genre)
        ? [for (final g in state.genres) if (g != genre) g]
        : [...state.genres, genre];
    state = state.copyWith(genres: genres);
  }

  void setSort(MovieSortBy sortBy, SortOrder order) {
    if (sortBy == state.sortBy && order == state.order) return;
    state = state.copyWith(sortBy: sortBy, order: order);
  }

  void reset() => state = const MovieQuery();
}

final movieQueryProvider = NotifierProvider<MovieQueryNotifier, MovieQuery>(
  MovieQueryNotifier.new,
);
