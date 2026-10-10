import '../../../../core/constants/app_constants.dart';
import '../entities/movie.dart';
import '../entities/movie_page.dart';
import '../entities/movie_query.dart';

/// What the app needs from the backend. Implementations throw a `Failure`
/// (see core/network/failures.dart) when something goes wrong.
abstract interface class MoviesRepository {
  Future<MoviePage> getMovies(MovieQuery query);

  Future<List<String>> getGenres();

  Future<MovieDetails> getMovieDetails(int id);

  Future<List<Recommendation>> getRecommendations(List<int> movieIds, {int limit = AppConstants.recommendationCount});
}
