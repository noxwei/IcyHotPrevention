import Foundation

/// Maps Finnhub DTOs to domain models.
enum FinnhubMapper {

    // MARK: - Public API

    /// Converts a ``FinnhubQuoteDTO`` into a domain ``IndexSnapshot`` for the given ticker.
    static func mapQuote(_ dto: FinnhubQuoteDTO, ticker: String) -> IndexSnapshot {
        let displayName = indexDisplayName(for: ticker)

        return IndexSnapshot(
            id: ticker.uppercased(),
            name: displayName,
            price: dto.c,
            change: dto.d,
            changePercent: dto.dp,
            high: dto.h,
            low: dto.l,
            previousClose: dto.pc
        )
    }

    /// Converts a ``FinnhubNewsDTO`` into a domain ``NewsItem``.
    static func mapNews(_ dto: FinnhubNewsDTO) -> NewsItem {
        let timestamp = Date(timeIntervalSince1970: TimeInterval(dto.datetime))
        let tickers = parseRelatedTickers(dto.related)
        let primaryTicker = tickers.first
        let category: NewsItem.NewsCategory = categorizeNews(dto.category, hasTicker: primaryTicker != nil)

        return NewsItem(
            id: UUID(),
            timestamp: timestamp,
            headline: dto.headline,
            source: dto.source,
            ticker: primaryTicker,
            url: URL(string: dto.url),
            category: category
        )
    }

    /// Converts a ``FinnhubCompanyDTO`` and ``FinnhubQuoteDTO`` into a domain ``MarketMover``.
    static func mapCompanyToMover(
        _ company: FinnhubCompanyDTO,
        quote: FinnhubQuoteDTO
    ) -> MarketMover {
        let ticker = company.ticker ?? ""
        let name = company.name ?? ticker

        return MarketMover(
            id: ticker,
            ticker: ticker,
            companyName: name,
            price: quote.c,
            changePercent: quote.dp,
            volume: 0,
            averageVolume: 0,
            sector: company.finnhubIndustry
        )
    }

    // MARK: - Helpers

    /// Parses a comma-separated string of tickers into an array, stripping whitespace
    /// and filtering out empty entries.
    private static func parseRelatedTickers(_ raw: String) -> [String] {
        guard !raw.isEmpty else { return [] }
        return raw
            .split(separator: ",")
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .filter { !$0.isEmpty }
    }

    /// Returns a human-readable index name for well-known ticker symbols,
    /// falling back to the ticker itself.
    private static func indexDisplayName(for ticker: String) -> String {
        let lookup: [String: String] = [
            "SPY": "S&P 500",
            "QQQ": "NASDAQ 100",
            "DIA": "Dow Jones",
            "IWM": "Russell 2000",
            "VTI": "Total Market"
        ]
        return lookup[ticker.uppercased()] ?? ticker.uppercased()
    }

    /// Determines the ``NewsItem.NewsCategory`` from the Finnhub category string.
    ///
    /// Finnhub typically returns `"general"`, `"forex"`, `"crypto"`, `"merger"`, or company-specific categories.
    private static func categorizeNews(_ category: String, hasTicker: Bool) -> NewsItem.NewsCategory {
        let lower = category.lowercased()

        if lower == "company news" || lower == "company" || hasTicker {
            return .corporate
        }

        switch lower {
        case "general", "forex", "crypto", "economy", "macro":
            return .macro
        case "merger", "ipo":
            return .corporate
        default:
            return hasTicker ? .corporate : .unknown
        }
    }
}
