import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_theme.dart';
import '../providers/movie_query_provider.dart';

/// Search box with a 350 ms debounce, so we call the API once the user pauses
/// typing instead of on every keystroke.
class MovieSearchField extends ConsumerStatefulWidget {
  const MovieSearchField({super.key});

  @override
  ConsumerState<MovieSearchField> createState() => _MovieSearchFieldState();
}

class _MovieSearchFieldState extends ConsumerState<MovieSearchField> {
  final _controller = TextEditingController();
  Timer? _debounce;

  @override
  void dispose() {
    _debounce?.cancel();
    _controller.dispose();
    super.dispose();
  }

  void _onChanged(String value) {
    _debounce?.cancel();
    _debounce = Timer(
      const Duration(milliseconds: 350),
      () => ref.read(movieQueryProvider.notifier).setSearch(value),
    );
    setState(() {}); // refresh the clear button
  }

  void _submit(String value) {
    _debounce?.cancel();
    ref.read(movieQueryProvider.notifier).setSearch(value);
  }

  void _clear() {
    _debounce?.cancel();
    _controller.clear();
    ref.read(movieQueryProvider.notifier).setSearch('');
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    // "Clear filters" elsewhere resets the query; keep the text box in sync.
    ref.listen<String>(movieQueryProvider.select((query) => query.search), (previous, next) {
      if (next.isEmpty && _controller.text.isNotEmpty) {
        _controller.clear();
        setState(() {});
      }
    });

    return TextField(
      controller: _controller,
      onChanged: _onChanged,
      onSubmitted: _submit,
      textInputAction: TextInputAction.search,
      decoration: InputDecoration(
        hintText: 'Search by title, director or cast',
        hintStyle: const TextStyle(color: AppColors.textSecondary),
        prefixIcon: const Icon(Icons.search_rounded),
        suffixIcon: _controller.text.isEmpty
            ? null
            : IconButton(
                tooltip: 'Clear search',
                icon: const Icon(Icons.close_rounded),
                onPressed: _clear,
              ),
        filled: true,
        fillColor: AppColors.surface,
        contentPadding: const EdgeInsets.symmetric(vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide.none,
        ),
      ),
    );
  }
}
