import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/dio_client.dart';
import '../../data/datasources/movies_remote_data_source.dart';
import '../../data/repositories/movies_repository_impl.dart';
import '../../domain/entities/movie.dart';
import '../../domain/repositories/movies_repository.dart';

final moviesRemoteDataSourceProvider = Provider<MoviesRemoteDataSource>(
  (ref) => MoviesRemoteDataSource(ref.watch(dioProvider)),
);

/// UI code depends on the [MoviesRepository] interface, never on Dio.
final moviesRepositoryProvider = Provider<MoviesRepository>(
  (ref) => MoviesRepositoryImpl(ref.watch(moviesRemoteDataSourceProvider)),
);

/// Genre names for the filter chips (loaded once, kept alive).
final genresProvider = FutureProvider<List<String>>(
  (ref) => ref.watch(moviesRepositoryProvider).getGenres(),
);

/// Full details of one movie; disposed when the details screen closes.
final movieDetailsProvider = FutureProvider.autoDispose.family<MovieDetails, int>(
  (ref, id) => ref.watch(moviesRepositoryProvider).getMovieDetails(id),
);
