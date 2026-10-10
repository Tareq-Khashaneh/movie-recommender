import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/core/utils/formatters.dart';
import 'package:frontend/core/utils/poster_url.dart';

void main() {
  group('PosterUrl.large', () {
    test('asks for a bigger image', () {
      const thumb = 'https://m.media-amazon.com/images/M/ABC@._V1_UX67_CR0,0,67,98_AL_.jpg';
      expect(
        PosterUrl.large(thumb),
        'https://m.media-amazon.com/images/M/ABC@._V1_UX500.jpg',
      );
    });

    test('leaves other urls alone and handles null/empty', () {
      expect(PosterUrl.large('https://example.com/a.jpg'), 'https://example.com/a.jpg');
      expect(PosterUrl.large(null), isNull);
      expect(PosterUrl.large(''), isNull);
    });
  });

  group('Formatters', () {
    test('runtime', () {
      expect(Formatters.runtime(142), '2h 22m');
      expect(Formatters.runtime(120), '2h');
      expect(Formatters.runtime(45), '45m');
      expect(Formatters.runtime(null), isNull);
    });

    test('compact numbers and money', () {
      expect(Formatters.compact(2943000), '2.9M');
      expect(Formatters.compact(1500), '1.5K');
      expect(Formatters.compact(950), '950');
      expect(Formatters.money(134966411), r'$135M');
    });
  });
}
