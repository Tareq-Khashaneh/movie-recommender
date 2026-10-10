import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/utils/poster_url.dart';

/// Poster with caching, a placeholder while loading, and a graceful fallback:
/// large version -> original thumbnail -> icon.
class PosterImage extends StatelessWidget {
  const PosterImage({super.key, required this.url, this.fit = BoxFit.cover});

  final String? url;
  final BoxFit fit;

  @override
  Widget build(BuildContext context) {
    final original = url;
    final large = PosterUrl.large(original);
    if (original == null || large == null) return const _PosterPlaceholder();

    return CachedNetworkImage(
      imageUrl: large,
      fit: fit,
      fadeInDuration: const Duration(milliseconds: 150),
      placeholder: (context, imageUrl) => const _PosterPlaceholder(),
      errorWidget: (context, imageUrl, error) {
        if (large == original) return const _PosterPlaceholder(isBroken: true);
        return CachedNetworkImage(
          imageUrl: original,
          fit: fit,
          errorWidget: (context, imageUrl, error) => const _PosterPlaceholder(isBroken: true),
        );
      },
    );
  }
}

class _PosterPlaceholder extends StatelessWidget {
  const _PosterPlaceholder({this.isBroken = false});

  final bool isBroken;

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: AppColors.surfaceHigh,
      child: Center(
        child: Icon(
          isBroken ? Icons.broken_image_outlined : Icons.movie_outlined,
          color: AppColors.textSecondary,
        ),
      ),
    );
  }
}
