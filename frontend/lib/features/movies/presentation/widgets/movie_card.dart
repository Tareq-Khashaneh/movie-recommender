import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../../domain/entities/movie.dart';
import 'poster_image.dart';

/// Shared by every movie grid so cards look identical and stay responsive:
/// as many columns as fit, each at most 190 logical pixels wide.
const movieGridDelegate = SliverGridDelegateWithMaxCrossAxisExtent(
  maxCrossAxisExtent: 190,
  mainAxisSpacing: 16,
  crossAxisSpacing: 12,
  childAspectRatio: 0.52,
);

/// Presentational movie card: poster, title, rating, year and genres.
/// It knows nothing about providers, so it is reused for selection and recommendations.
class MovieCard extends StatelessWidget {
  const MovieCard({
    super.key,
    required this.movie,
    required this.onTap,
    this.isSelected = false,
    this.showSelectionIndicator = false,
    this.onInfoTap,
    this.badge,
  });

  final Movie movie;
  final VoidCallback onTap;
  final bool isSelected;
  final bool showSelectionIndicator;
  final VoidCallback? onInfoTap;
  final String? badge;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    const radius = BorderRadius.all(Radius.circular(14));

    return Semantics(
      button: true,
      selected: isSelected,
      label: movie.title,
      child: InkWell(
        onTap: onTap,
        borderRadius: radius,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Stack(
                fit: StackFit.expand,
                children: [
                  Hero(
                    tag: 'poster-${movie.id}',
                    child: ClipRRect(
                      borderRadius: radius,
                      child: PosterImage(url: movie.posterUrl),
                    ),
                  ),
                  if (isSelected)
                    Positioned.fill(
                      child: IgnorePointer(
                        child: DecoratedBox(
                          decoration: BoxDecoration(
                            borderRadius: radius,
                            border: Border.all(color: AppColors.accent, width: 3),
                          ),
                        ),
                      ),
                    ),
                  if (showSelectionIndicator)
                    Positioned(top: 8, right: 8, child: _SelectionIndicator(isSelected: isSelected)),
                  if (onInfoTap != null)
                    Positioned(top: 4, left: 4, child: _InfoButton(onTap: onInfoTap!)),
                  if (badge != null) Positioned(left: 8, bottom: 8, child: _Badge(text: badge!)),
                ],
              ),
            ),
            const SizedBox(height: 8),
            Text(
              movie.title,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 2),
            Row(
              children: [
                const Icon(Icons.star_rounded, size: 16, color: AppColors.rating),
                const SizedBox(width: 3),
                Text(movie.imdbRating.toStringAsFixed(1), style: textTheme.bodySmall),
                if (movie.year != null) ...[
                  const SizedBox(width: 8),
                  Text(
                    '${movie.year}',
                    style: textTheme.bodySmall?.copyWith(color: AppColors.textSecondary),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 2),
            Text(
              movie.genresLabel,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: textTheme.bodySmall?.copyWith(color: AppColors.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}

class _SelectionIndicator extends StatelessWidget {
  const _SelectionIndicator({required this.isSelected});

  final bool isSelected;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 26,
      height: 26,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: isSelected ? AppColors.accent : Colors.black54,
        border: Border.all(color: isSelected ? AppColors.accent : Colors.white70, width: 1.5),
      ),
      child: isSelected ? const Icon(Icons.check_rounded, size: 18, color: Colors.white) : null,
    );
  }
}

class _InfoButton extends StatelessWidget {
  const _InfoButton({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: 'Movie details',
      onPressed: onTap,
      iconSize: 18,
      visualDensity: VisualDensity.compact,
      style: IconButton.styleFrom(backgroundColor: Colors.black54),
      icon: const Icon(Icons.info_outline_rounded, color: Colors.white),
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: Colors.black.withAlpha(180),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        child: Text(
          text,
          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.white),
        ),
      ),
    );
  }
}
