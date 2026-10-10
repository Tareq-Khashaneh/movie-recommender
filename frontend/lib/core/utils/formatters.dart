/// Small display helpers for numbers coming from the API.
abstract final class Formatters {
  /// 142 -> "2h 22m", 45 -> "45m", null -> null.
  static String? runtime(int? minutes) {
    if (minutes == null || minutes <= 0) return null;
    final hours = minutes ~/ 60;
    final rest = minutes % 60;
    if (hours == 0) return '${rest}m';
    return rest == 0 ? '${hours}h' : '${hours}h ${rest}m';
  }

  /// 2943000 -> "2.9M", 1500 -> "1.5K".
  static String compact(int value) {
    if (value >= 1000000000) return '${_trim(value / 1000000000)}B';
    if (value >= 1000000) return '${_trim(value / 1000000)}M';
    if (value >= 1000) return '${_trim(value / 1000)}K';
    return '$value';
  }

  static String money(int value) => '\$${compact(value)}';

  static String _trim(double value) =>
      value.toStringAsFixed(1).replaceAll(RegExp(r'\.0$'), '');
}
