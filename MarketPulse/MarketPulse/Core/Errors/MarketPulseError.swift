import Foundation

/// Unified error type for all MarketPulse operations.
enum MarketPulseError: Error, LocalizedError, Sendable {
    /// HTTP request failed with the given status code and optional server message.
    case networkError(statusCode: Int, message: String?)

    /// CSV data could not be parsed. The associated value describes the failure.
    case csvParsingError(String)

    /// JSON decoding failed. The original `DecodingError` (or other) is preserved.
    case jsonDecodingError(Error)

    /// A required API key is missing for the named service.
    case apiKeyMissing(String)

    /// The requested operation is not supported by the named data source.
    case notSupportedBySource(String)

    /// A cache read/write operation failed.
    case cacheError(String)

    /// A Keychain read/write/delete operation failed.
    case keychainError(String)

    /// An AI text-generation request failed.
    case aiGenerationFailed(String)

    /// The upstream API rate limit has been exceeded.
    case rateLimitExceeded

    /// A catch-all for truly unexpected failures.
    case unexpected(String)

    // MARK: - LocalizedError

    var errorDescription: String? {
        switch self {
        case .networkError(let statusCode, let message):
            let base = "Network error (HTTP \(statusCode))"
            if let message, !message.isEmpty {
                return "\(base): \(message)"
            }
            return base

        case .csvParsingError(let detail):
            return "CSV parsing error: \(detail)"

        case .jsonDecodingError(let underlying):
            return "JSON decoding error: \(underlying.localizedDescription)"

        case .apiKeyMissing(let service):
            return "API key missing for \(service). Please add it in Settings."

        case .notSupportedBySource(let source):
            return "Operation not supported by \(source)"

        case .cacheError(let detail):
            return "Cache error: \(detail)"

        case .keychainError(let detail):
            return "Keychain error: \(detail)"

        case .aiGenerationFailed(let detail):
            return "AI generation failed: \(detail)"

        case .rateLimitExceeded:
            return "Rate limit exceeded. Please wait before making another request."

        case .unexpected(let detail):
            return "Unexpected error: \(detail)"
        }
    }
}

// MARK: - Equatable (best-effort, ignoring associated Error values)

extension MarketPulseError: Equatable {
    static func == (lhs: MarketPulseError, rhs: MarketPulseError) -> Bool {
        switch (lhs, rhs) {
        case (.networkError(let lCode, let lMsg), .networkError(let rCode, let rMsg)):
            return lCode == rCode && lMsg == rMsg
        case (.csvParsingError(let l), .csvParsingError(let r)):
            return l == r
        case (.jsonDecodingError, .jsonDecodingError):
            // Cannot meaningfully compare arbitrary Error values.
            return true
        case (.apiKeyMissing(let l), .apiKeyMissing(let r)):
            return l == r
        case (.notSupportedBySource(let l), .notSupportedBySource(let r)):
            return l == r
        case (.cacheError(let l), .cacheError(let r)):
            return l == r
        case (.keychainError(let l), .keychainError(let r)):
            return l == r
        case (.aiGenerationFailed(let l), .aiGenerationFailed(let r)):
            return l == r
        case (.rateLimitExceeded, .rateLimitExceeded):
            return true
        case (.unexpected(let l), .unexpected(let r)):
            return l == r
        default:
            return false
        }
    }
}
