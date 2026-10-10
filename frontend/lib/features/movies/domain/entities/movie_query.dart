import '../../../../core/constants/app_constants.dart';

enum MovieSortBy { rating, year, title, votes }

enum SortOrder { asc, desc }

/// What the user is currently asking the catalog for.
class MovieQuery {
  const MovieQuery({
    this.page = 1,
    this.pageSize = AppConstants.pageSize,
    this.search = '',
    this.genres = const [],
    this.sortBy = MovieSortBy.rating,
    this.order = SortOrder.desc,
  });

  final int page;
  final int pageSize;
  final String search;
  final List<String> genres;
  final MovieSortBy sortBy;
  final SortOrder order;

  MovieQuery copyWith({
    int? page,
    int? pageSize,
    String? search,
    List<String>? genres,
    MovieSortBy? sortBy,
    SortOrder? order,
  }) {
    return MovieQuery(
      page: page ?? this.page,
      pageSize: pageSize ?? this.pageSize,
      search: search ?? this.search,
      genres: genres ?? this.genres,
      sortBy: sortBy ?? this.sortBy,
      order: order ?? this.order,
    );
  }
}
