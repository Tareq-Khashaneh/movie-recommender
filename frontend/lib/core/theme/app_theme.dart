import 'package:flutter/material.dart';

abstract final class AppColors {
  static const Color background = Color(0xFF0B0C10);
  static const Color surface = Color(0xFF16181F);
  static const Color surfaceHigh = Color(0xFF1F222B);
  static const Color accent = Color(0xFFFF4D5A);
  static const Color accentSoft = Color(0x33FF4D5A);
  static const Color rating = Color(0xFFFFC53D);
  static const Color textPrimary = Color(0xFFF2F3F5);
  static const Color textSecondary = Color(0xFF9AA0AD);
}

ThemeData buildDarkTheme() {
  const scheme = ColorScheme.dark(
    primary: AppColors.accent,
    onPrimary: Colors.white,
    secondary: AppColors.rating,
    surface: AppColors.surface,
    onSurface: AppColors.textPrimary,
    error: Color(0xFFFF6B6B),
  );

  final base = ThemeData(useMaterial3: true, colorScheme: scheme);

  return base.copyWith(
    scaffoldBackgroundColor: AppColors.background,
    textTheme: base.textTheme.apply(
      bodyColor: AppColors.textPrimary,
      displayColor: AppColors.textPrimary,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: AppColors.background,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      centerTitle: false,
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        minimumSize: const Size.fromHeight(52),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
    ),
  );
}
