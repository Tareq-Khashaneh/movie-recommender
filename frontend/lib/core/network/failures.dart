import 'package:dio/dio.dart';

/// Every error the UI can see. Repositories throw these (never raw Dio errors),
/// so screens only need to show `failure.message`.
sealed class Failure implements Exception {
  const Failure(this.message);

  final String message;

  @override
  String toString() => message;
}

final class NetworkFailure extends Failure {
  const NetworkFailure()
      : super('Cannot reach the server. Check your connection and make sure the backend is running.');
}

final class TimeoutFailure extends Failure {
  const TimeoutFailure() : super('The server took too long to respond. Please try again.');
}

final class ServerFailure extends Failure {
  const ServerFailure(super.message, {this.statusCode});

  final int? statusCode;
}

final class InvalidResponseFailure extends Failure {
  const InvalidResponseFailure() : super('The server returned an unexpected response.');
}

final class UnknownFailure extends Failure {
  const UnknownFailure() : super('Something went wrong. Please try again.');
}

/// Translates a Dio error into one of our [Failure] types.
Failure failureFromDio(DioException e) {
  return switch (e.type) {
    DioExceptionType.connectionTimeout ||
    DioExceptionType.sendTimeout ||
    DioExceptionType.receiveTimeout ||
    DioExceptionType.transformTimeout =>
      const TimeoutFailure(),
    DioExceptionType.connectionError => const NetworkFailure(),
    DioExceptionType.badResponse => ServerFailure(
        _apiMessage(e.response?.data) ?? 'Server error (${e.response?.statusCode}).',
        statusCode: e.response?.statusCode,
      ),
    // badCertificate, cancel, unknown and any type a future Dio version adds.
    _ => const UnknownFailure(),
  };
}

/// The backend always answers errors as {"error": {"code": ..., "message": ...}}.
String? _apiMessage(Object? data) {
  if (data is Map<String, dynamic>) {
    final error = data['error'];
    if (error is Map<String, dynamic> && error['message'] is String) {
      return error['message'] as String;
    }
  }
  return null;
}

/// A message that is safe to show the user for any error object.
String errorMessage(Object error) =>
    error is Failure ? error.message : const UnknownFailure().message;
