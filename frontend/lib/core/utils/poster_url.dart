/// The dataset stores tiny 67x98 IMDb thumbnails. Amazon image URLs accept a
/// size suffix, so we ask for a larger version and keep the original as the
/// fallback (the image widget falls back to it if the large one fails).
abstract final class PosterUrl {
  static final RegExp _sizeSuffix = RegExp(r'\._V1_.*\.jpg$');

  static String? large(String? url, {int width = 500}) {
    if (url == null || url.isEmpty) return null;
    if (!_sizeSuffix.hasMatch(url)) return url;
    return url.replaceFirst(_sizeSuffix, '._V1_UX$width.jpg');
  }
}
