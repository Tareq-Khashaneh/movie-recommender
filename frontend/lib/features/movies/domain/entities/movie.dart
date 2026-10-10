/// A movie as shown on a card (list, grid, selection strip).
class Movie {
  const Movie({
    required this.id,
    required this.title,
    required this.posterUrl,
    required this.year,
    required this.genres,
    required this.imdbRating,
  });

  final int id;
  final String title;
  final String? posterUrl;
  final int? year;
  final List<String> genres;
  final double imdbRating;

  String get genresLabel => genres.join(' • ');

  // Identity is the backend id, so a Movie can live in a Set/Map for selection.
  @override
  bool operator ==(Object other) => other is Movie && other.id == id;

  @override
  int get hashCode => id.hashCode;
}

/// Everything the details screen needs. Every optional field can be null
/// because the dataset has gaps (certificate, meta score, gross...).
class MovieDetails extends Movie {
  const MovieDetails({
    required super.id,
    required super.title,
    required super.posterUrl,
    required super.year,
    required super.genres,
    required super.imdbRating,
    required this.certificate,
    required this.runtimeMinutes,
    required this.overview,
    required this.metaScore,
    required this.director,
    required this.cast,
    required this.votes,
    required this.gross,
  });

  final String? certificate;
  final int? runtimeMinutes;
  final String? overview;
  final int? metaScore;
  final String? director;
  final List<String> cast;
  final int? votes;
  final int? gross;
}

/// A recommended movie plus how well it matched the user's selection.
class Recommendation {
  const Recommendation({
    required this.movie,
    required this.similarity,
    required this.score,
  });

  final Movie movie;

  /// Genre similarity to the selection, 0..1.
  final double similarity;

  /// Final ranking score (70% similarity + 30% normalised rating).
  final double score;
}
