import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/features/movies/domain/entities/movie.dart';
import 'package:frontend/features/movies/presentation/providers/selection_provider.dart';

Movie _movie(int id) => Movie(
      id: id,
      title: 'Movie $id',
      posterUrl: null,
      year: 2000,
      genres: const ['Drama'],
      imdbRating: 7.0,
    );

void main() {
  test('selection is capped at 5 and can be toggled off', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);
    final notifier = container.read(selectedMoviesProvider.notifier);

    for (var id = 1; id <= 5; id++) {
      expect(notifier.toggle(_movie(id)), isTrue);
    }
    expect(container.read(selectedMoviesProvider), hasLength(5));

    // A 6th movie is rejected.
    expect(notifier.toggle(_movie(6)), isFalse);
    expect(container.read(selectedMoviesProvider), hasLength(5));

    // Tapping a selected movie removes it, keeping the order of the others.
    expect(notifier.toggle(_movie(3)), isTrue);
    expect(container.read(selectedMoviesProvider).map((m) => m.id), [1, 2, 4, 5]);

    notifier.clear();
    expect(container.read(selectedMoviesProvider), isEmpty);
  });
}
