import '../../domain/entities/movie_page.dart';
import 'movie_model.dart';

class MoviePageModel extends MoviePage {
  const MoviePageModel({
    required super.items,
    required super.page,
    required super.pageSize,
    required super.total,
    required super.totalPages,
    required super.hasNext,
    required super.hasPrevious,
  });

  factory MoviePageModel.fromJson(Map<String, dynamic> json) {
    return MoviePageModel(
      items: (json['items'] as List)
          .map((item) => MovieModel.fromJson(item as Map<String, dynamic>))
          .toList(growable: false),
      page: json['page'] as int,
      pageSize: json['page_size'] as int,
      total: json['total'] as int,
      totalPages: json['total_pages'] as int,
      hasNext: json['has_next'] as bool,
      hasPrevious: json['has_previous'] as bool,
    );
  }
}
