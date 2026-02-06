import Foundation

/// A multi-format date parser that recognises the most common date
/// representations encountered in financial data feeds.
///
/// Supported formats:
/// - ISO 8601 full:       `2025-01-15T14:30:00Z`
/// - ISO 8601 with offset:`2025-01-15T14:30:00+05:00`
/// - ISO 8601 date only:  `2025-01-15`
/// - US slash:            `01/15/2025`
/// - Medium English:      `Jan 15, 2025`
/// - FINVIZ style:        `Jan-15-25 04:30PM`
/// - Unix timestamp:      `1705334400` (as a String; seconds since epoch)
struct DateParser: Sendable {

    // MARK: - Public API

    /// Attempts to parse the given string into a `Date` by trying every
    /// known format in order of specificity.
    ///
    /// - Parameter string: The date string to parse.
    /// - Returns: A `Date` if any format matched, otherwise `nil`.
    static func parse(_ string: String) -> Date? {
        let trimmed = string.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return nil }

        // 1. Try the built-in ISO 8601 parser first (handles full ISO with
        //    fractional seconds, offsets, and 'Z').
        if let date = iso8601Formatter.date(from: trimmed) {
            return date
        }

        // 2. Walk through the explicit DateFormatter-based patterns.
        for formatter in orderedFormatters {
            if let date = formatter.date(from: trimmed) {
                return date
            }
        }

        // 3. Try interpreting as a Unix timestamp (integer or decimal seconds).
        if let timestamp = Double(trimmed), timestamp > 946_684_800 {
            // Guard: only accept values after 2000-01-01 to avoid
            // misinterpreting small numbers or IDs as timestamps.
            return Date(timeIntervalSince1970: timestamp)
        }

        return nil
    }

    // MARK: - Formatters (lazily initialized, thread-safe via `let`)

    /// ISO 8601 formatter with fractional seconds support.
    private static let iso8601Formatter: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [
            .withInternetDateTime,
            .withFractionalSeconds
        ]
        return f
    }()

    /// Date formatters ordered from most-specific to least-specific so the
    /// first match is likely the correct interpretation.
    private static let orderedFormatters: [DateFormatter] = {
        let patterns: [(String, TimeZone?)] = [
            // ISO 8601 without fractional seconds (fallback for the ISO8601DateFormatter).
            ("yyyy-MM-dd'T'HH:mm:ssZ",       nil),
            ("yyyy-MM-dd'T'HH:mm:ssXXXXX",   nil),
            ("yyyy-MM-dd'T'HH:mm:ss",        TimeZone(identifier: "UTC")),

            // FINVIZ: "Jan-15-25 04:30PM"
            ("MMM-dd-yy hh:mma",             TimeZone(identifier: "America/New_York")),

            // Medium English: "Jan 15, 2025"
            ("MMM dd, yyyy",                 TimeZone(identifier: "UTC")),

            // Date only: "2025-01-15"
            ("yyyy-MM-dd",                   TimeZone(identifier: "UTC")),

            // US slash: "01/15/2025"
            ("MM/dd/yyyy",                   TimeZone(identifier: "UTC")),
        ]

        return patterns.map { pattern, tz in
            let formatter = DateFormatter()
            formatter.locale = Locale(identifier: "en_US_POSIX")
            formatter.dateFormat = pattern
            if let tz {
                formatter.timeZone = tz
            }
            return formatter
        }
    }()
}
