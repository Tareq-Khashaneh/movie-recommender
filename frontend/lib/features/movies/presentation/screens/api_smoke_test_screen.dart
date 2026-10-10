// TEMPORARY screen for Step 1: proves the app can talk to the real backend.
// It is replaced by the real Movie Selection screen in Step 3.
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/api_config.dart';
import '../../../../core/network/failures.dart';
import '../../domain/entities/movie_query.dart';
import '../providers/movies_providers.dart';

final _smokeTestProvider = FutureProvider.autoDispose<List<String>>((ref) async {
  final repo = ref.watch(moviesRepositoryProvider);

  final page = await repo.getMovies(const MovieQuery(pageSize: 3));
  final genres = await repo.getGenres();
  final details = await repo.getMovieDetails(966);
  final recs = await repo.getRecommendations(const [1, 2, 8, 20, 30], limit: 3);

  return [
    'GET /movies  ->  ${page.total} movies, ${page.totalPages} pages. First: ${page.items.first.title}',
    'GET /movies/genres  ->  ${genres.length} genres',
    'GET /movies/966  ->  ${details.title} (${details.year}), ${details.runtimeMinutes} min, ${details.director}',
    'POST /recommendations  ->  ${recs.map((r) => r.movie.title).join(', ')}',
  ];
});

class ApiSmokeTestScreen extends ConsumerWidget {
  const ApiSmokeTestScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final result = ref.watch(_smokeTestProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('API connection check')),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Backend: ${ApiConfig.baseUrl}'),
            const SizedBox(height: 16),
            Expanded(
              child: result.when(
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (error, _) => Center(
                  child: Text(
                    error is Failure ? error.message : '$error',
                    style: TextStyle(color: Theme.of(context).colorScheme.error),
                  ),
                ),
                data: (lines) => ListView(
                  children: [
                    for (final line in lines)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: Text(line),
                      ),
                  ],
                ),
              ),
            ),
            FilledButton(
              onPressed: () => ref.invalidate(_smokeTestProvider),
              child: const Text('Run again'),
            ),
          ],
        ),
      ),
    );
  }
}
