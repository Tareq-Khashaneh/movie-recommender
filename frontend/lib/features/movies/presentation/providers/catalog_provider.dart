import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/failures.dart';
import '../../domain/entities/movie.dart';
import 'movie_query_provider.dart';
import 'movies_providers.dart';

/// Everything the movie grid needs: the pages loaded so far plus paging flags.
class CatalogState {
  const CatalogState({
    required this.items,
    required this.total,
    required this.page,
    required this.hasNext,
    this.isLoadingMore = false,
    this.loadMoreFailure,
  });

  final List<Movie> items;
  final int total;
  final int page;
  final bool hasNext;
  final bool isLoadingMore;
  final Failure? loadMoreFailure;

  CatalogState copyWith({
    List<Movie>? items,
    int? page,
    bool? hasNext,
    bool? isLoadingMore,
    Failure? loadMoreFailure,
    bool clearLoadMoreFailure = false,
  }) {
    return CatalogState(
      items: items ?? this.items,
      total: total,
      page: page ?? this.page,
      hasNext: hasNext ?? this.hasNext,
      isLoadingMore: isLoadingMore ?? this.isLoadingMore,
      loadMoreFailure: clearLoadMoreFailure ? null : (loadMoreFailure ?? this.loadMoreFailure),
    );
  }
}

/// Loads page 1 for the current query (reloading whenever the query changes)
/// and appends further pages on demand (infinite scroll).
class CatalogNotifier extends AsyncNotifier<CatalogState> {
  // Bumped on every reload so a slow "load more" for an old query is ignored.
  int _generation = 0;

  @override
  Future<CatalogState> build() async {
    _generation++;
    final query = ref.watch(movieQueryProvider);
    final page = await ref.watch(moviesRepositoryProvider).getMovies(query);
    return CatalogState(
      items: page.items,
      total: page.total,
      page: page.page,
      hasNext: page.hasNext,
    );
  }

  /// Fetches the next page. Automatic calls are skipped after a failure;
  /// the "Retry" button passes [isRetry] to try again.
  Future<void> loadMore({bool isRetry = false}) async {
    final current = state.value;
    if (current == null || !current.hasNext || current.isLoadingMore) return;
    if (current.loadMoreFailure != null && !isRetry) return;

    final generation = _generation;
    state = AsyncData(current.copyWith(isLoadingMore: true, clearLoadMoreFailure: true));

    try {
      final query = ref.read(movieQueryProvider).copyWith(page: current.page + 1);
      final page = await ref.read(moviesRepositoryProvider).getMovies(query);
      if (generation != _generation) return;
      state = AsyncData(
        current.copyWith(
          items: [...current.items, ...page.items],
          page: page.page,
          hasNext: page.hasNext,
          isLoadingMore: false,
        ),
      );
    } catch (error) {
      if (generation != _generation) return;
      state = AsyncData(
        current.copyWith(
          isLoadingMore: false,
          loadMoreFailure: error is Failure ? error : const UnknownFailure(),
        ),
      );
    }
  }
}

final catalogProvider = AsyncNotifierProvider<CatalogNotifier, CatalogState>(
  CatalogNotifier.new,
);
