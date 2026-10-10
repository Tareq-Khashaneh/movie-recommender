import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/entities/movie_query.dart';
import '../providers/movie_query_provider.dart';

enum SortOption {
  topRated('Top rated', MovieSortBy.rating, SortOrder.desc),
  newest('Newest first', MovieSortBy.year, SortOrder.desc),
  oldest('Oldest first', MovieSortBy.year, SortOrder.asc),
  mostVoted('Most voted', MovieSortBy.votes, SortOrder.desc),
  titleAZ('Title A-Z', MovieSortBy.title, SortOrder.asc);

  const SortOption(this.label, this.sortBy, this.order);

  final String label;
  final MovieSortBy sortBy;
  final SortOrder order;
}

class SortMenuButton extends ConsumerWidget {
  const SortMenuButton({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sort = ref.watch(movieQueryProvider.select((query) => (query.sortBy, query.order)));
    final current = SortOption.values.firstWhere(
      (option) => option.sortBy == sort.$1 && option.order == sort.$2,
      orElse: () => SortOption.topRated,
    );

    return PopupMenuButton<SortOption>(
      tooltip: 'Sort',
      icon: const Icon(Icons.sort_rounded),
      onSelected: (option) =>
          ref.read(movieQueryProvider.notifier).setSort(option.sortBy, option.order),
      itemBuilder: (context) => [
        for (final option in SortOption.values)
          CheckedPopupMenuItem<SortOption>(
            value: option,
            checked: option == current,
            child: Text(option.label),
          ),
      ],
    );
  }
}
