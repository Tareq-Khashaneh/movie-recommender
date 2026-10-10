import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/core/theme/app_theme.dart';
import 'package:frontend/features/movies/domain/entities/movie.dart';
import 'package:frontend/features/movies/presentation/widgets/movie_card.dart';

void main() {
  testWidgets('MovieCard shows its data and reacts to taps', (tester) async {
    var taps = 0;
    const movie = Movie(
      id: 1,
      title: 'Inception',
      posterUrl: null,
      year: 2010,
      genres: ['Action', 'Sci-Fi'],
      imdbRating: 8.8,
    );

    await tester.pumpWidget(
      MaterialApp(
        theme: buildDarkTheme(),
        home: Scaffold(
          body: SizedBox(
            width: 180,
            height: 340,
            child: MovieCard(movie: movie, onTap: () => taps++),
          ),
        ),
      ),
    );

    expect(find.text('Inception'), findsOneWidget);
    expect(find.text('8.8'), findsOneWidget);
    expect(find.text('2010'), findsOneWidget);
    expect(find.text('Action • Sci-Fi'), findsOneWidget);

    await tester.tap(find.byType(MovieCard));
    expect(taps, 1);
  });
}
