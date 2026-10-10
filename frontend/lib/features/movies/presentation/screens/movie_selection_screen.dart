import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/network/failures.dart';
import '../../../../core/theme/app_theme.dart';
import '../providers/catalog_provider.dart';
import '../providers/movie_query_provider.dart';
import '../widgets/genre_filter_bar.dart';
import '../widgets/movie_card.dart';
import '../widgets/movie_search_field.dart';
import '../widgets/selectable_movie_card.dart';
import '../widgets/selection_bar.dart';
import '../widgets/sort_menu_button.dart';
import '../widgets/state_views.dart';
import 'recommendations_screen.dart';

/// Screen 1: search/filter the catalog and pick exactly 5 movies.
class MovieSelectionScreen extends ConsumerWidget {
  const MovieSelectionScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Hide the bottom panel while the keyboard is open so the list keeps its space.
    final isKeyboardOpen = MediaQuery.viewInsetsOf(context).bottom > 0;

    return Scaffold(
      appBar: AppBar(
        title: const Text(AppConstants.appName),
        actions: const [SortMenuButton()],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text(
                "Pick ${AppConstants.requiredSelectionCount} movies you like and we'll find what to watch next.",
                style: Theme.of(context)
                    .textTheme
                    .bodyMedium
                    ?.copyWith(color: AppColors.textSecondary),
              ),
            ),
          ),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: MovieSearchField(),
          ),
          const SizedBox(height: 12),
          const GenreFilterBar(),
          const SizedBox(height: 8),
          const Expanded(child: _CatalogView()),
          if (!isKeyboardOpen) SelectionBar(onContinue: () => RecommendationsScreen.open(context)),
        ],
      ),
    );
  }
}

class _CatalogView extends ConsumerWidget {
  const _CatalogView();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final catalog = ref.watch(catalogProvider);

    return Stack(
      children: [
        catalog.when(
          // Keep showing the previous results while a new search/filter loads.
          skipLoadingOnReload: true,
          loading: () => const LoadingView(message: 'Loading movies…'),
          error: (error, _) => ErrorView(
            message: errorMessage(error),
            onRetry: () => ref.invalidate(catalogProvider),
          ),
          data: (state) => _MovieGrid(state: state),
        ),
        if (catalog.isLoading && catalog.hasValue)
          const Align(
            alignment: Alignment.topCenter,
            child: LinearProgressIndicator(minHeight: 2),
          ),
      ],
    );
  }
}

class _MovieGrid extends ConsumerStatefulWidget {
  const _MovieGrid({required this.state});

  final CatalogState state;

  @override
  ConsumerState<_MovieGrid> createState() => _MovieGridState();
}

class _MovieGridState extends ConsumerState<_MovieGrid> {
  final _controller = ScrollController();

  @override
  void initState() {
    super.initState();
    _controller.addListener(_loadMoreIfNearEnd);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _loadMoreIfNearEnd() {
    if (!_controller.hasClients) return;
    final position = _controller.position;
    if (!position.hasContentDimensions) return;
    if (position.extentAfter < 600) {
      ref.read(catalogProvider.notifier).loadMore();
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = widget.state;

    if (state.items.isEmpty) {
      return EmptyView(
        icon: Icons.search_off_rounded,
        title: 'No movies found',
        message: 'Try a different search or remove some filters.',
        actionLabel: 'Clear filters',
        onAction: () => ref.read(movieQueryProvider.notifier).reset(),
      );
    }

    // Covers screens so large that the first page does not even scroll.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _loadMoreIfNearEnd();
    });

    return CustomScrollView(
      controller: _controller,
      slivers: [
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
          sliver: SliverGrid.builder(
            gridDelegate: movieGridDelegate,
            itemCount: state.items.length,
            itemBuilder: (context, index) {
              final movie = state.items[index];
              return SelectableMovieCard(key: ValueKey(movie.id), movie: movie);
            },
          ),
        ),
        SliverToBoxAdapter(child: _GridFooter(state: state)),
      ],
    );
  }
}

class _GridFooter extends ConsumerWidget {
  const _GridFooter({required this.state});

  final CatalogState state;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final failure = state.loadMoreFailure;

    if (failure != null) {
      return Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Text(failure.message, textAlign: TextAlign.center),
            TextButton(
              onPressed: () => ref.read(catalogProvider.notifier).loadMore(isRetry: true),
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (state.isLoadingMore) {
      return const Padding(
        padding: EdgeInsets.all(24),
        child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
      );
    }

    if (!state.hasNext) {
      return Padding(
        padding: const EdgeInsets.all(24),
        child: Center(
          child: Text(
            '${state.total} movies',
            style: const TextStyle(color: AppColors.textSecondary),
          ),
        ),
      );
    }

    return const SizedBox(height: 24);
  }
}
