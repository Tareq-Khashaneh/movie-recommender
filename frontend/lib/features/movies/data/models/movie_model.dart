import '../../domain/entities/movie.dart';

/// JSON <-> entity mapping. Field names match the FastAPI responses exactly.
class MovieModel extends Movie {
  const MovieModel({
    required super.id,
    required super.title,
    required super.posterUrl,
    required super.year,
    required super.genres,
    required super.imdbRating,
  });

  factory MovieModel.fromJson(Map<String, dynamic> json) {
    return MovieModel(
      id: json['id'] as int,
      title: json['title'] as String,
      posterUrl: json['poster_url'] as String?,
      year: json['year'] as int?,
      genres: List<String>.from(json['genres'] as List),
      imdbRating: (json['imdb_rating'] as num).toDouble(),
    );
  }
}

class MovieDetailsModel extends MovieDetails {
  const MovieDetailsModel({
    required super.id,
    required super.title,
    required super.posterUrl,
    required super.year,
    required super.genres,
    required super.imdbRating,
    required super.certificate,
    required super.runtimeMinutes,
    required super.overview,
    required super.metaScore,
    required super.director,
    required super.cast,
    required super.votes,
    required super.gross,
  });

  factory MovieDetailsModel.fromJson(Map<String, dynamic> json) {
    final base = MovieModel.fromJson(json);
    return MovieDetailsModel(
      id: base.id,
      title: base.title,
      posterUrl: base.posterUrl,
      year: base.year,
      genres: base.genres,
      imdbRating: base.imdbRating,
      certificate: json['certificate'] as String?,
      runtimeMinutes: json['runtime_minutes'] as int?,
      overview: json['overview'] as String?,
      metaScore: json['meta_score'] as int?,
      director: json['director'] as String?,
      cast: List<String>.from(json['cast'] as List),
      votes: json['votes'] as int?,
      gross: json['gross'] as int?,
    );
  }
}

class RecommendationModel extends Recommendation {
  const RecommendationModel({
    required super.movie,
    required super.similarity,
    required super.score,
  });

  /// A recommendation item is a normal movie card plus `similarity` and `score`.
  factory RecommendationModel.fromJson(Map<String, dynamic> json) {
    return RecommendationModel(
      movie: MovieModel.fromJson(json),
      similarity: (json['similarity'] as num).toDouble(),
      score: (json['score'] as num).toDouble(),
    );
  }
}
