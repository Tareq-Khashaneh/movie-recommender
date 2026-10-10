import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/utils/formatters.dart';
import '../../domain/entities/movie.dart';

/// The part of the details screen that comes from GET /movies/{id}.
/// Every field is optional because the dataset has gaps.
class DetailsContent extends StatelessWidget {
  const DetailsContent({super.key, required this.details});

  final MovieDetails details;

  @override
  Widget build(BuildContext context) {
    final overview = details.overview?.trim();
    final director = details.director;
    final stats = <(String, String)>[
      if (details.votes != null) ('IMDb votes', Formatters.compact(details.votes!)),
      if (details.metaScore != null) ('Metascore', '${details.metaScore}/100'),
      if (details.gross != null) ('Box office', Formatters.money(details.gross!)),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (overview != null && overview.isNotEmpty) ...[
          _Section(
            title: 'Overview',
            child: Text(
              overview,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    height: 1.5,
                    color: AppColors.textSecondary,
                  ),
            ),
          ),
          const SizedBox(height: 24),
        ],
        if (director != null && director.isNotEmpty) ...[
          _Section(title: 'Director', child: Text(director)),
          const SizedBox(height: 24),
        ],
        if (details.cast.isNotEmpty) ...[
          _Section(title: 'Cast', child: Text(details.cast.join(', '))),
          const SizedBox(height: 24),
        ],
        if (stats.isNotEmpty)
          Row(
            children: [
              for (final stat in stats) Expanded(child: _StatTile(label: stat.$1, value: stat.$2)),
            ],
          ),
      ],
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 8),
        child,
      ],
    );
  }
}

class _StatTile extends StatelessWidget {
  const _StatTile({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 4),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        children: [
          Text(value, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
          const SizedBox(height: 4),
          Text(label, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
        ],
      ),
    );
  }
}
