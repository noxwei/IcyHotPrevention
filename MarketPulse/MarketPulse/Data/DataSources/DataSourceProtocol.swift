import Foundation

// MARK: - MarketDataSourceProtocol

/// Unified contract for any external market-data provider (Finviz, Finnhub, etc.).
///
/// Each conforming type represents a single upstream API. Methods that are not
/// supported by a given provider should throw
/// ``MarketPulseError/notSupportedBySource(_:)`` rather than returning empty
/// arrays, so callers can distinguish "no data available" from "not implemented."
protocol MarketDataSourceProtocol: Sendable {

    /// A short, stable identifier for logging and cache-key namespacing
    /// (e.g. `"finviz"`, `"finnhub"`).
    var sourceIdentifier: String { get }

    /// Fetches the latest market news headlines.
    func fetchNews() async throws -> [NewsItem]

    /// Fetches real-time (or near-real-time) quote snapshots for the given tickers.
    func fetchQuotes(tickers: [String]) async throws -> [IndexSnapshot]

    /// Fetches today's biggest gainers and losers.
    func fetchTopMovers() async throws -> [MarketMover]

    /// Fetches sector-level performance data with leading tickers per sector.
    func fetchSectorPerformance() async throws -> [SectorRotation]

    /// Fetches the user's saved portfolio / watchlist tickers.
    func fetchPortfolio() async throws -> [KeyTicker]
}
