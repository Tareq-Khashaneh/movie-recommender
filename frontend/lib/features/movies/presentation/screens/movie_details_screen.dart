import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/failures.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/utils/formatters.dart';
import '../../domain/entities/movie.dart';
import '../providers/movies_providers.dart';
import '../widgets/details_content.dart';
import '../widgets/info_pill.dart';
import '../widgets/poster_image.dart';
import '../widgets/state_views.dart';

/// Screen 3. The card data we already have (poster, title, rating, genres) shows
/// instantly; the rest (overview, cast, runtime...) loads from GET /movies/{id}.
class MovieDetailsScreen extends ConsumerWidget {
  const MovieDetailsScreen({super.key, required this.movie});

  final Movie movie;

  static Future<void> open(BuildContext context, Movie movie) {
    return Navigator.of(context).push(
      MaterialPageRoute<void>(builder: (_) => MovieDetailsScreen(movie: movie)),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final details = ref.watch(movieDetailsProvider(movie.id));
    final loaded = details.value;
    final runtime = Formatters.runtime(loaded?.runtimeMinutes);
    final certificate = loaded?.certificate;

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            pinned: true,
            expandedHeight: 460,
            backgroundColor: AppColors.background,
            leading: Padding(
              padding: const EdgeInsets.all(6),
              child: IconButton(
                tooltip: 'Back',
                onPressed: () => Navigator.of(context).maybePop(),
                style: IconButton.styleFrom(backgroundColor: Colors.black54),
                icon: const Icon(Icons.arrow_back_rounded, color: Colors.white),
              ),
            ),
            flexibleSpace: FlexibleSpaceBar(background: _PosterHeader(movie: movie)),
          ),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    movie.title,
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      InfoPill(
                        icon: Icons.star_rounded,
                        iconColor: AppColors.rating,
                        label: '${movie.imdbRating.toStringAsFixed(1)} / 10',
                      ),
                      if (movie.year != null) InfoPill(label: '${movie.year}'),
                      if (runtime != null) InfoPill(icon: Icons.schedule_rounded, label: runtime),
                      if (certificate != null && certificate.isNotEmpty) InfoPill(label: certificate),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [for (final genre in movie.genres) InfoPill(label: genre)],
                  ),
                  const SizedBox(height: 24),
                  details.when(
                    loading: () => const Padding(
                      padding: EdgeInsets.symmetric(vertical: 24),
                      child: Center(child: CircularProgressIndicator()),
                    ),
                    error: (error, _) => ErrorView(
                      message: errorMessage(error),
                      onRetry: () => ref.invalidate(movieDetailsProvider(movie.id)),
                    ),
                    data: (data) => DetailsContent(details: data),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PosterHeader extends StatelessWidget {
  const _PosterHeader({required this.movie});

  final Movie movie;

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        Hero(
          tag: 'poster-${movie.id}',
          child: PosterImage(url: movie.posterUrl),
        ),
        const DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.center,
              end: Alignment.bottomCenter,
              colors: [Colors.transparent, AppColors.background],
            ),
          ),
        ),
      ],
    );
  }
}
