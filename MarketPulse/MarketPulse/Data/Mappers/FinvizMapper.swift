import Foundation

/// Maps FINVIZ DTOs to domain models.
enum FinvizMapper {

    // MARK: - Public API

    /// Converts a ``FinvizNewsDTO`` into a domain ``NewsItem``.
    static func mapNewsRow(_ dto: FinvizNewsDTO) -> NewsItem {
        let timestamp = parseFinvizDateTime(date: dto.date, time: dto.time)
        let category: NewsItem.NewsCategory = dto.ticker != nil ? .corporate : .macro

        return NewsItem(
            id: UUID(),
            timestamp: timestamp,
            headline: dto.title,
            source: dto.source,
            ticker: dto.ticker,
            url: URL(string: dto.link),
            category: category
        )
    }

    /// Converts a ``FinvizPortfolioDTO`` into a domain ``KeyTicker``.
    static func mapPortfolioRow(_ dto: FinvizPortfolioDTO) -> KeyTicker {
        let priceValue = parseDouble(dto.price)
        let changeValue = parseChangePercent(dto.change)

        return KeyTicker(
            id: dto.ticker,
            ticker: dto.ticker,
            price: priceValue,
            changePercent: changeValue,
            note: dto.sector
        )
    }

    /// Converts a ``FinvizPortfolioDTO`` into a domain ``MarketMover``.
    static func mapPortfolioToMover(_ dto: FinvizPortfolioDTO) -> MarketMover {
        let priceValue = parseDouble(dto.price)
        let changeValue = parseChangePercent(dto.change)
        let volumeValue = parseVolume(dto.volume)

        return MarketMover(
            id: dto.ticker,
            ticker: dto.ticker,
            companyName: dto.company,
            price: priceValue,
            changePercent: changeValue,
            volume: volumeValue,
            averageVolume: 0,
            sector: dto.sector
        )
    }

    /// Converts a ``FinvizPortfolioDTO`` into a domain ``IndexSnapshot`` if the ticker
    /// represents a major index ETF (SPY, QQQ, DIA). Returns `nil` otherwise.
    static func mapPortfolioToIndex(_ dto: FinvizPortfolioDTO) -> IndexSnapshot? {
        let indexNames: [String: String] = [
            "SPY": "S&P 500",
            "QQQ": "NASDAQ 100",
            "DIA": "Dow Jones"
        ]

        let upperTicker = dto.ticker.uppercased()
        guard let displayName = indexNames[upperTicker] else {
            return nil
        }

        let priceValue = parseDouble(dto.price)
        let changePercent = parseChangePercent(dto.change)
        let change = priceValue * changePercent / 100.0
        let previousClose = priceValue - change

        return IndexSnapshot(
            id: upperTicker,
            name: displayName,
            price: priceValue,
            change: change,
            changePercent: changePercent,
            high: priceValue,
            low: priceValue,
            previousClose: previousClose
        )
    }

    // MARK: - Parsing Helpers

    /// Parses a FINVIZ date/time pair into a `Date`.
    ///
    /// FINVIZ uses formats like "Jan-02-25" or "2025-01-02" for dates and "08:30AM" or "08:30" for times.
    private static func parseFinvizDateTime(date: String, time: String?) -> Date {
        let dateTimeString: String
        if let time, !time.isEmpty {
            dateTimeString = "\(date) \(time)"
        } else {
            dateTimeString = date
        }

        // Try multiple known FINVIZ date/time formats
        let formatters = makeDateFormatters()
        for formatter in formatters {
            if let parsed = formatter.date(from: dateTimeString) {
                return parsed
            }
        }

        // Fallback: try date-only formats
        let dateOnlyFormatters = makeDateOnlyFormatters()
        for formatter in dateOnlyFormatters {
            if let parsed = formatter.date(from: date) {
                return parsed
            }
        }

        return Date()
    }

    private static func makeDateFormatters() -> [DateFormatter] {
        let formats = [
            "MMM-dd-yy hh:mma",
            "MMM-dd-yy HH:mm",
            "yyyy-MM-dd hh:mma",
            "yyyy-MM-dd HH:mm",
            "MM/dd/yyyy hh:mma",
            "MM/dd/yyyy HH:mm"
        ]
        return formats.map { format in
            let formatter = DateFormatter()
            formatter.dateFormat = format
            formatter.locale = Locale(identifier: "en_US_POSIX")
            return formatter
        }
    }

    private static func makeDateOnlyFormatters() -> [DateFormatter] {
        let formats = [
            "MMM-dd-yy",
            "yyyy-MM-dd",
            "MM/dd/yyyy"
        ]
        return formats.map { format in
            let formatter = DateFormatter()
            formatter.dateFormat = format
            formatter.locale = Locale(identifier: "en_US_POSIX")
            return formatter
        }
    }

    /// Parses a percentage string like `"5.23%"`, `"-2.10%"`, or `"5.23"` into a `Double`.
    /// Returns `0` for malformed input.
    private static func parseChangePercent(_ raw: String) -> Double {
        let cleaned = raw
            .trimmingCharacters(in: .whitespaces)
            .replacingOccurrences(of: "%", with: "")
        return Double(cleaned) ?? 0
    }

    /// Parses a volume string that may contain commas or SI suffixes (K, M, B).
    /// Examples: `"51,800,000"`, `"51.8M"`, `"200K"`, `"1.2B"`.
    /// Returns `0` for malformed input.
    private static func parseVolume(_ raw: String) -> Double {
        let trimmed = raw.trimmingCharacters(in: .whitespaces).uppercased()

        if trimmed.hasSuffix("B") {
            let numeric = String(trimmed.dropLast())
            return (Double(numeric) ?? 0) * 1_000_000_000
        } else if trimmed.hasSuffix("M") {
            let numeric = String(trimmed.dropLast())
            return (Double(numeric) ?? 0) * 1_000_000
        } else if trimmed.hasSuffix("K") {
            let numeric = String(trimmed.dropLast())
            return (Double(numeric) ?? 0) * 1_000
        }

        let cleaned = trimmed.replacingOccurrences(of: ",", with: "")
        return Double(cleaned) ?? 0
    }

    /// Parses a plain numeric string, stripping commas and whitespace.
    /// Returns `0` for malformed input.
    private static func parseDouble(_ raw: String) -> Double {
        let cleaned = raw
            .trimmingCharacters(in: .whitespaces)
            .replacingOccurrences(of: ",", with: "")
            .replacingOccurrences(of: "$", with: "")
        return Double(cleaned) ?? 0
    }

    /// Parses a market-cap string like `"1.2B"`, `"500M"`, `"15.3T"`.
    /// Also handles plain numeric strings with commas.
    /// Returns `0` for malformed input.
    static func parseMarketCap(_ raw: String) -> Double {
        let trimmed = raw.trimmingCharacters(in: .whitespaces).uppercased()

        if trimmed.hasSuffix("T") {
            let numeric = String(trimmed.dropLast())
            return (Double(numeric) ?? 0) * 1_000_000_000_000
        } else if trimmed.hasSuffix("B") {
            let numeric = String(trimmed.dropLast())
            return (Double(numeric) ?? 0) * 1_000_000_000
        } else if trimmed.hasSuffix("M") {
            let numeric = String(trimmed.dropLast())
            return (Double(numeric) ?? 0) * 1_000_000
        } else if trimmed.hasSuffix("K") {
            let numeric = String(trimmed.dropLast())
            return (Double(numeric) ?? 0) * 1_000
        }

        let cleaned = trimmed.replacingOccurrences(of: ",", with: "")
        return Double(cleaned) ?? 0
    }
}
