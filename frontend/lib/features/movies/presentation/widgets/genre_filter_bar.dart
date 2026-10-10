import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_theme.dart';
import '../providers/movie_query_provider.dart';
import '../providers/movies_providers.dart';

/// Horizontally scrolling genre chips. Selecting several genres narrows the
/// results (a movie must have all of them).
class GenreFilterBar extends ConsumerWidget {
  const GenreFilterBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final genres = ref.watch(genresProvider);
    final selected = ref.watch(movieQueryProvider.select((query) => query.genres));

    return SizedBox(
      height: 40,
      child: genres.when(
        loading: () => const SizedBox.shrink(),
        error: (error, _) => Align(
          alignment: Alignment.centerLeft,
          child: TextButton.icon(
            onPressed: () => ref.invalidate(genresProvider),
            icon: const Icon(Icons.refresh_rounded, size: 18),
            label: const Text("Couldn't load genres. Tap to retry"),
          ),
        ),
        data: (items) => ListView.separated(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 16),
          itemCount: items.length,
          separatorBuilder: (context, index) => const SizedBox(width: 8),
          itemBuilder: (context, index) {
            final genre = items[index];
            final isOn = selected.contains(genre);
            return FilterChip(
              label: Text(genre),
              selected: isOn,
              showCheckmark: false,
              onSelected: (_) => ref.read(movieQueryProvider.notifier).toggleGenre(genre),
              backgroundColor: AppColors.surface,
              selectedColor: AppColors.accentSoft,
              shape: const StadiumBorder(),
              side: BorderSide(color: isOn ? AppColors.accent : AppColors.surfaceHigh),
              labelStyle: TextStyle(
                color: isOn ? AppColors.textPrimary : AppColors.textSecondary,
                fontWeight: FontWeight.w500,
              ),
            );
          },
        ),
      ),
    );
  }
}
