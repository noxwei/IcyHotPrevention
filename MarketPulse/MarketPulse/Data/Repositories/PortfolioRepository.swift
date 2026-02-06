import Foundation

// MARK: - Protocol

/// Repository contract for portfolio / watchlist queries.
protocol PortfolioRepositoryProtocol: Sendable {
    /// Returns all tickers in the user's portfolio.
    func fetchPortfolio() async throws -> [KeyTicker]

    /// Returns the detail for a single ticker, or `nil` if not found.
    func fetchTickerDetail(_ ticker: String) async throws -> KeyTicker?
}

// MARK: - Implementation

/// Concrete portfolio repository backed by a single ``MarketDataSourceProtocol``
/// with actor-based caching.
final class PortfolioRepository: PortfolioRepositoryProtocol, @unchecked Sendable {

    // MARK: - Dependencies

    private let primarySource: any MarketDataSourceProtocol
    private let cache: CacheManager

    // MARK: - Cache Configuration

    private enum CacheConfig {
        static let portfolioKey = "portfolio.all"
        static func tickerDetailKey(_ ticker: String) -> String {
            "portfolio.ticker.\(ticker.uppercased())"
        }

        static let portfolioTTL: TimeInterval     = 600  // 10 min
        static let tickerDetailTTL: TimeInterval   = 600  // 10 min
    }

    // MARK: - Init

    init(
        primarySource: any MarketDataSourceProtocol,
        cache: CacheManager
    ) {
        self.primarySource = primarySource
        self.cache = cache
    }

    // MARK: - PortfolioRepositoryProtocol

    func fetchPortfolio() async throws -> [KeyTicker] {
        if let cached: [KeyTicker] = await cache.get(key: CacheConfig.portfolioKey) {
            return cached
        }

        let tickers = try await primarySource.fetchPortfolio()

        await cache.set(
            key: CacheConfig.portfolioKey,
            value: tickers,
            ttl: CacheConfig.portfolioTTL
        )

        return tickers
    }

    func fetchTickerDetail(_ ticker: String) async throws -> KeyTicker? {
        let cacheKey = CacheConfig.tickerDetailKey(ticker)

        // Try the per-ticker cache first.
        if let cached: KeyTicker = await cache.get(key: cacheKey) {
            return cached
        }

        // Fetch the full portfolio (may come from the portfolio cache),
        // then locate the requested ticker.
        let portfolio = try await fetchPortfolio()

        let uppercasedTicker = ticker.uppercased()
        let match = portfolio.first { $0.ticker.uppercased() == uppercasedTicker }

        if let match {
            await cache.set(
                key: cacheKey,
                value: match,
                ttl: CacheConfig.tickerDetailTTL
            )
        }

        return match
    }
}
