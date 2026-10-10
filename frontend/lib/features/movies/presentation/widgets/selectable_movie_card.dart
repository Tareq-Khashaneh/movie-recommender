import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/app_constants.dart';
import '../../domain/entities/movie.dart';
import '../providers/selection_provider.dart';
import '../screens/movie_details_screen.dart';
import 'movie_card.dart';

/// A [MovieCard] wired to the selection state. It watches only "is THIS movie
/// selected", so toggling one card does not rebuild the rest of the grid.
class SelectableMovieCard extends ConsumerWidget {
  const SelectableMovieCard({super.key, required this.movie});

  final Movie movie;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isSelected = ref.watch(selectedMoviesProvider.select((movies) => movies.contains(movie)));

    return MovieCard(
      movie: movie,
      isSelected: isSelected,
      showSelectionIndicator: true,
      onInfoTap: () => MovieDetailsScreen.open(context, movie),
      onTap: () {
        final changed = ref.read(selectedMoviesProvider.notifier).toggle(movie);
        if (!changed) {
          ScaffoldMessenger.of(context)
            ..hideCurrentSnackBar()
            ..showSnackBar(
              const SnackBar(
                content: Text(
                  'You can select up to ${AppConstants.requiredSelectionCount} movies. Remove one first.',
                ),
              ),
            );
        }
      },
    );
  }
}
