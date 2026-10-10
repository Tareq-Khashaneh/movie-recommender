import 'package:dio/dio.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/network/failures.dart';
import '../../domain/entities/movie.dart';
import '../../domain/entities/movie_page.dart';
import '../../domain/entities/movie_query.dart';
import '../../domain/repositories/movies_repository.dart';
import '../datasources/movies_remote_data_source.dart';

class MoviesRepositoryImpl implements MoviesRepository {
  MoviesRepositoryImpl(this._remote);

  final MoviesRemoteDataSource _remote;

  @override
  Future<MoviePage> getMovies(MovieQuery query) => _guard(() => _remote.fetchMovies(query));

  @override
  Future<List<String>> getGenres() => _guard(_remote.fetchGenres);

  @override
  Future<MovieDetails> getMovieDetails(int id) => _guard(() => _remote.fetchMovieDetails(id));

  @override
  Future<List<Recommendation>> getRecommendations(
    List<int> movieIds, {
    int limit = AppConstants.recommendationCount,
  }) {
    return _guard(() => _remote.fetchRecommendations(movieIds, limit));
  }

  /// The single place where low-level errors become [Failure]s, so the
  /// conversion logic is not duplicated per endpoint.
  Future<T> _guard<T>(Future<T> Function() request) async {
    try {
      return await request();
    } on Failure {
      rethrow;
    } on DioException catch (e) {
      throw failureFromDio(e);
    } catch (_) {
      // Missing/wrongly-typed JSON fields (TypeError, FormatException...).
      throw const InvalidResponseFailure();
    }
  }
}
