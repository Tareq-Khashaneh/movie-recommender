import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/constants/app_constants.dart';
import 'core/theme/app_theme.dart';
import 'features/movies/presentation/screens/movie_selection_screen.dart';

void main() async{

  WidgetsFlutterBinding.ensureInitialized();

  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
  ]);
  runApp(
    ProviderScope(
      // Riverpod 3 silently retries failed providers by default. We want the
      // error screen (with its own "Try again" button) to appear immediately.
      retry: (retryCount, error) => null,
      child: const MovieRecommenderApp(),
    ),
  );
}

class MovieRecommenderApp extends StatelessWidget {
  const MovieRecommenderApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: AppConstants.appName,
      debugShowCheckedModeBanner: false,
      theme: buildDarkTheme(),
      home: const MovieSelectionScreen(),
    );
  }
}
