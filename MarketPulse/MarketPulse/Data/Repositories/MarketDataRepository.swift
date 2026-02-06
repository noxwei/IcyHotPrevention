import Foundation

// MARK: - Protocol

/// Repository contract for aggregate market data used by the daily scan screen.
protocol MarketDataRepositoryProtocol: Sendable {
    func fetchNews() async throws -> [NewsItem]
    func fetchIndexSnapshots() async throws -> [IndexSnapshot]
    func fetchTopMovers() async throws -> [MarketMover]
    func fetchSectorRotation() async throws -> [SectorRotation]
    func fetchPortfolio() async throws -> [KeyTicker]
}

// MARK: - Implementation

/// Concrete repository that orchestrates primary/secondary data sources with
/// caching. Each data category has its own TTL to balance freshness against
/// upstream rate limits.
final class MarketDataRepository: MarketDataRepositoryProtocol, @unchecked Sendable {

    // MARK: - Dependencies

    private let primarySource: any MarketDataSourceProtocol
    private let secondarySource: (any MarketDataSourceProtocol)?
    private let cache: CacheManager

    // MARK: - Cache Keys & TTLs (seconds)

    private enum CacheConfig {
        static let newsKey        = "repo.news"
        static let indexKey       = "repo.indexSnapshots"
        static let moversKey      = "repo.topMovers"
        static let sectorsKey     = "repo.sectorRotation"
        static let portfolioKey   = "repo.portfolio"

        static let newsTTL: TimeInterval        = 600   // 10 min
        static let indexTTL: TimeInterval        = 300   // 5 min
        static let moversTTL: TimeInterval       = 300   // 5 min
        static let sectorsTTL: TimeInterval      = 900   // 15 min
        static let portfolioTTL: TimeInterval    = 600   // 10 min
    }

    // MARK: - Default Index Tickers

    /// The ETF tickers used for the index-snapshot widget.
    private let defaultIndexTickers = ["SPY", "QQQ", "DIA"]

    // MARK: - Init

    init(
        primarySource: any MarketDataSourceProtocol,
        secondarySource: (any MarketDataSourceProtocol)?,
        cache: CacheManager
    ) {
        self.primarySource = primarySource
        self.secondarySource = secondarySource
        self.cache = cache
    }

    // MARK: - MarketDataRepositoryProtocol

    func fetchNews() async throws -> [NewsItem] {
        if let cached: [NewsItem] = await cache.get(key: CacheConfig.newsKey) {
            return cached
        }

        let items = try await fetchWithFallback { source in
            try await source.fetchNews()
        }

        await cache.set(key: CacheConfig.newsKey, value: items, ttl: CacheConfig.newsTTL)
        return items
    }

    func fetchIndexSnapshots() async throws -> [IndexSnapshot] {
        if let cached: [IndexSnapshot] = await cache.get(key: CacheConfig.indexKey) {
            return cached
        }

        let snapshots = try await fetchWithFallback { source in
            try await source.fetchQuotes(tickers: self.defaultIndexTickers)
        }

        await cache.set(key: CacheConfig.indexKey, value: snapshots, ttl: CacheConfig.indexTTL)
        return snapshots
    }

    func fetchTopMovers() async throws -> [MarketMover] {
        if let cached: [MarketMover] = await cache.get(key: CacheConfig.moversKey) {
            return cached
        }

        let movers = try await fetchWithFallback { source in
            try await source.fetchTopMovers()
        }

        await cache.set(key: CacheConfig.moversKey, value: movers, ttl: CacheConfig.moversTTL)
        return movers
    }

    func fetchSectorRotation() async throws -> [SectorRotation] {
        if let cached: [SectorRotation] = await cache.get(key: CacheConfig.sectorsKey) {
            return cached
        }

        let sectors = try await fetchWithFallback { source in
            try await source.fetchSectorPerformance()
        }

        await cache.set(key: CacheConfig.sectorsKey, value: sectors, ttl: CacheConfig.sectorsTTL)
        return sectors
    }

    func fetchPortfolio() async throws -> [KeyTicker] {
        if let cached: [KeyTicker] = await cache.get(key: CacheConfig.portfolioKey) {
            return cached
        }

        let tickers = try await fetchWithFallback { source in
            try await source.fetchPortfolio()
        }

        await cache.set(key: CacheConfig.portfolioKey, value: tickers, ttl: CacheConfig.portfolioTTL)
        return tickers
    }

    // MARK: - Private Helpers

    /// Attempts to fetch data from the primary source. On failure, retries
    /// with the secondary source if one is configured. If both fail, the
    /// error from the primary source is thrown.
    private func fetchWithFallback<T>(
        _ operation: (any MarketDataSourceProtocol) async throws -> T
    ) async throws -> T {
        do {
            return try await operation(primarySource)
        } catch {
            guard let secondary = secondarySource else {
                throw error
            }

            // If the primary simply does not support this operation,
            // try the secondary before giving up.
            do {
                return try await operation(secondary)
            } catch {
                // Surface the secondary error when both fail, since the
                // primary already indicated it couldn't handle the request.
                throw error
            }
        }
    }
}
