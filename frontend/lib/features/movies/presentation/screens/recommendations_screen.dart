import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/failures.dart';
import '../../../../core/theme/app_theme.dart';
import '../../domain/entities/movie.dart';
import '../providers/recommendations_provider.dart';
import '../providers/selection_provider.dart';
import '../widgets/movie_card.dart';
import '../widgets/state_views.dart';
import 'movie_details_screen.dart';

/// Screen 2: movies similar to the 5 picks, shown as a grid of cards.
class RecommendationsScreen extends ConsumerWidget {
  const RecommendationsScreen({super.key});

  static Future<void> open(BuildContext context) {
    return Navigator.of(context).push(
      MaterialPageRoute<void>(builder: (_) => const RecommendationsScreen()),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recommendations = ref.watch(recommendationsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Recommended for You'),
        actions: [
          TextButton(
            onPressed: () {
              ref.read(selectedMoviesProvider.notifier).clear();
              Navigator.of(context).pop();
            },
            child: const Text('Start over'),
          ),
        ],
      ),
      body: recommendations.when(
        loading: () => const LoadingView(message: "Finding movies you'll love…"),
        error: (error, _) => ErrorView(
          message: errorMessage(error),
          onRetry: () => ref.invalidate(recommendationsProvider),
        ),
        data: (items) => items.isEmpty
            ? EmptyView(
                icon: Icons.movie_filter_outlined,
                title: 'No recommendations found',
                message: "We couldn't find similar movies. Try picking different ones.",
                actionLabel: 'Pick different movies',
                onAction: () => Navigator.of(context).pop(),
              )
            : _RecommendationGrid(items: items),
      ),
    );
  }
}

class _RecommendationGrid extends ConsumerWidget {
  const _RecommendationGrid({required this.items});

  final List<Recommendation> items;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // read (not watch): "Start over" clears the selection while this screen is still closing.
    final basedOn = ref.read(selectedMoviesProvider).map((movie) => movie.title).join(', ');

    return CustomScrollView(
      slivers: [
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
            child: Text(
              'Based on: $basedOn',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: AppColors.textSecondary),
            ),
          ),
        ),
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
          sliver: SliverGrid.builder(
            gridDelegate: movieGridDelegate,
            itemCount: items.length,
            itemBuilder: (context, index) {
              final recommendation = items[index];
              return MovieCard(
                key: ValueKey(recommendation.movie.id),
                movie: recommendation.movie,
                badge: '${(recommendation.similarity * 100).round()}% match',
                onTap: () => MovieDetailsScreen.open(context, recommendation.movie),
              );
            },
          ),
        ),
      ],
    );
  }
}
