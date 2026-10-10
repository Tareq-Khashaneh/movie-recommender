import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/entities/movie.dart';
import 'movies_providers.dart';
import 'selection_provider.dart';

/// Asks the backend for recommendations based on the current selection.
/// Auto-disposed, so every visit to the recommendations screen fetches fresh results.
final recommendationsProvider = FutureProvider.autoDispose<List<Recommendation>>((ref) {
  final movieIds = ref.read(selectedMoviesProvider).map((movie) => movie.id).toList(growable: false);
  return ref.watch(moviesRepositoryProvider).getRecommendations(movieIds);
});
