import Foundation

/// A generic, zero-dependency CSV parser that maps rows to dictionaries or
/// domain models. Handles quoted fields, embedded newlines, and BOM markers.
struct CSVParser: Sendable {

    // MARK: - Public API

    /// Parses raw CSV data into an array of `[columnName: value]` dictionaries.
    ///
    /// - Parameters:
    ///   - data: The raw CSV bytes.
    ///   - encoding: String encoding to apply (defaults to UTF-8).
    /// - Returns: One dictionary per data row, keyed by the header names.
    /// - Throws: `MarketPulseError.csvParsingError` on any failure.
    static func parse(
        data: Data,
        encoding: String.Encoding = .utf8
    ) throws -> [[String: String]] {
        let text = try decodedText(from: data, encoding: encoding)
        let rows = splitLogicalRows(text)

        guard let headerRow = rows.first else {
            throw MarketPulseError.csvParsingError("CSV data is empty — no header row found.")
        }

        let headers = headerRow
            .csvComponents(separator: ",")
            .map { $0.csvUnescaped.trimmingCharacters(in: .whitespacesAndNewlines) }

        guard !headers.isEmpty else {
            throw MarketPulseError.csvParsingError("CSV header row contains no columns.")
        }

        var results: [[String: String]] = []
        results.reserveCapacity(rows.count - 1)

        for rowIndex in 1..<rows.count {
            let row = rows[rowIndex]

            // Skip blank trailing rows.
            let trimmed = row.trimmingCharacters(in: .whitespacesAndNewlines)
            if trimmed.isEmpty { continue }

            let fields = row.csvComponents(separator: ",")

            var dict: [String: String] = [:]
            dict.reserveCapacity(headers.count)

            for (columnIndex, header) in headers.enumerated() {
                if columnIndex < fields.count {
                    dict[header] = fields[columnIndex].csvUnescaped
                } else {
                    dict[header] = ""
                }
            }

            results.append(dict)
        }

        return results
    }

    /// Parses CSV data and maps each row through a caller-supplied transform.
    ///
    /// Rows for which `map` returns `nil` are silently skipped, which is useful
    /// for filtering out malformed or irrelevant entries.
    ///
    /// - Parameters:
    ///   - data: The raw CSV bytes.
    ///   - encoding: String encoding to apply (defaults to UTF-8).
    ///   - map: A closure that converts a `[columnName: value]` dictionary into
    ///     the desired model type, or returns `nil` to skip the row.
    /// - Returns: An array of successfully mapped models.
    /// - Throws: `MarketPulseError.csvParsingError` on structural CSV failures,
    ///   or rethrows errors from the `map` closure.
    static func parse<T>(
        data: Data,
        encoding: String.Encoding = .utf8,
        map: ([String: String]) throws -> T?
    ) throws -> [T] {
        let dictionaries = try parse(data: data, encoding: encoding)
        var results: [T] = []
        results.reserveCapacity(dictionaries.count)

        for dict in dictionaries {
            if let model = try map(dict) {
                results.append(model)
            }
        }

        return results
    }

    // MARK: - Internal Helpers

    /// Decodes raw data to a String, stripping any leading UTF-8 BOM.
    private static func decodedText(
        from data: Data,
        encoding: String.Encoding
    ) throws -> String {
        var cleanData = data

        // Strip UTF-8 BOM (EF BB BF) if present.
        let bom: [UInt8] = [0xEF, 0xBB, 0xBF]
        if cleanData.count >= 3 {
            let prefix = [UInt8](cleanData.prefix(3))
            if prefix == bom {
                cleanData = cleanData.dropFirst(3)
            }
        }

        guard let text = String(data: cleanData, encoding: encoding) else {
            throw MarketPulseError.csvParsingError(
                "Unable to decode CSV data with encoding \(encoding)."
            )
        }

        return text
    }

    /// Splits a CSV string into logical rows, correctly keeping quoted fields
    /// that contain embedded newlines as part of the same row.
    private static func splitLogicalRows(_ text: String) -> [String] {
        var rows: [String] = []
        var current = ""
        var insideQuotes = false

        // Normalize line endings to \n.
        let normalized = text
            .replacingOccurrences(of: "\r\n", with: "\n")
            .replacingOccurrences(of: "\r", with: "\n")

        for char in normalized {
            if char == "\"" {
                insideQuotes.toggle()
                current.append(char)
            } else if char == "\n" && !insideQuotes {
                rows.append(current)
                current = ""
            } else {
                current.append(char)
            }
        }

        // Append last row if non-empty.
        if !current.isEmpty {
            rows.append(current)
        }

        return rows
    }
}
