import 'package:dio/dio.dart';

import '../../domain/entities/movie_query.dart';
import '../models/movie_model.dart';
import '../models/movie_page_model.dart';

/// The only class that knows the endpoint URLs and JSON shapes.
/// It does HTTP + parsing and lets errors bubble up; the repository translates them.
class MoviesRemoteDataSource {
  MoviesRemoteDataSource(this._dio);

  final Dio _dio;

  Future<MoviePageModel> fetchMovies(MovieQuery query) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/movies',
      queryParameters: {
        'page': query.page,
        'page_size': query.pageSize,
        if (query.search.trim().isNotEmpty) 'search': query.search.trim(),
        if (query.genres.isNotEmpty) 'genre': query.genres,
        'sort_by': query.sortBy.name,
        'order': query.order.name,
      },
    );
    return MoviePageModel.fromJson(response.data!);
  }

  Future<List<String>> fetchGenres() async {
    final response = await _dio.get<List<dynamic>>('/movies/genres');
    return List<String>.from(response.data!);
  }

  Future<MovieDetailsModel> fetchMovieDetails(int id) async {
    final response = await _dio.get<Map<String, dynamic>>('/movies/$id');
    return MovieDetailsModel.fromJson(response.data!);
  }

  Future<List<RecommendationModel>> fetchRecommendations(
    List<int> movieIds,
    int limit,
  ) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/recommendations',
      data: {'movie_ids': movieIds, 'limit': limit},
    );
    return (response.data!['items'] as List)
        .map((item) => RecommendationModel.fromJson(item as Map<String, dynamic>))
        .toList(growable: false);
  }
}
