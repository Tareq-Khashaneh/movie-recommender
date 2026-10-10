import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/app_constants.dart';
import '../../domain/entities/movie.dart';

/// The movies the user has picked, in the order they picked them (max 5).
class SelectedMoviesNotifier extends Notifier<List<Movie>> {
  @override
  List<Movie> build() => const [];

  bool get isFull => state.length >= AppConstants.requiredSelectionCount;

  /// Adds or removes [movie]. Returns false when it could not be added
  /// because 5 movies are already selected.
  bool toggle(Movie movie) {
    if (state.contains(movie)) {
      remove(movie);
      return true;
    }
    if (isFull) return false;
    state = [...state, movie];
    return true;
  }

  void remove(Movie movie) {
    state = [for (final m in state) if (m != movie) m];
  }

  void clear() => state = const [];
}

final selectedMoviesProvider = NotifierProvider<SelectedMoviesNotifier, List<Movie>>(
  SelectedMoviesNotifier.new,
);
