import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../../domain/entities/movie.dart';
import '../providers/selection_provider.dart';
import 'poster_image.dart';

/// Bottom panel: "3 / 5 movies selected", thumbnails of the picks (tap to remove)
/// and the button that stays disabled until exactly 5 movies are selected.
class SelectionBar extends ConsumerWidget {
  const SelectionBar({super.key, required this.onContinue});

  final VoidCallback onContinue;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selected = ref.watch(selectedMoviesProvider);
    const requiredCount = AppConstants.requiredSelectionCount;
    final notifier = ref.read(selectedMoviesProvider.notifier);

    return DecoratedBox(
      decoration: const BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                children: [
                  Text(
                    '${selected.length} / $requiredCount movies selected',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600),
                  ),
                  const Spacer(),
                  if (selected.isNotEmpty) TextButton(onPressed: notifier.clear, child: const Text('Clear')),
                ],
              ),
              const SizedBox(height: 6),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  for (var i = 0; i < requiredCount; i++) ...[
                    if (i > 0) const SizedBox(width: 10),
                    _Slot(
                      movie: i < selected.length ? selected[i] : null,
                      onRemove: () => notifier.remove(selected[i]),
                    ),
                  ],
                ],
              ),
              const SizedBox(height: 14),
              FilledButton(
                onPressed: selected.length == requiredCount ? onContinue : null,
                child: const Text('Get recommendations'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Slot extends StatelessWidget {
  const _Slot({required this.movie, required this.onRemove});

  final Movie? movie;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) {
    final picked = movie;
    const radius = BorderRadius.all(Radius.circular(8));

    return SizedBox(
      width: 43,
      height: 64,
      child: picked == null
          ? DecoratedBox(
              decoration: BoxDecoration(
                borderRadius: radius,
                border: Border.all(color: AppColors.surfaceHigh, width: 1.5),
              ),
              child: const Icon(Icons.add_rounded, size: 16, color: AppColors.textSecondary),
            )
          : Semantics(
              button: true,
              label: 'Remove ${picked.title}',
              child: GestureDetector(
                onTap: onRemove,
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    ClipRRect(borderRadius: radius, child: PosterImage(url: picked.posterUrl)),
                    Positioned(
                      top: 2,
                      right: 2,
                      child: DecoratedBox(
                        decoration: const BoxDecoration(shape: BoxShape.circle, color: Colors.black87),
                        child: const Padding(
                          padding: EdgeInsets.all(2),
                          child: Icon(Icons.close_rounded, size: 12, color: Colors.white),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}
