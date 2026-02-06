import Foundation

// MARK: - Protocol

/// Repository contract for news-specific queries.
protocol NewsRepositoryProtocol: Sendable {
    /// Returns all recent news items, newest first.
    func fetchAllNews() async throws -> [NewsItem]

    /// Returns news items associated with a specific ticker symbol, newest first.
    func fetchNewsByTicker(_ ticker: String) async throws -> [NewsItem]
}

// MARK: - Implementation

/// Concrete news repository backed by a single ``MarketDataSourceProtocol``
/// with actor-based caching.
final class NewsRepository: NewsRepositoryProtocol, @unchecked Sendable {

    // MARK: - Dependencies

    private let primarySource: any MarketDataSourceProtocol
    private let cache: CacheManager

    // MARK: - Cache Configuration

    private enum CacheConfig {
        static let allNewsKey = "news.all"
        static func tickerKey(_ ticker: String) -> String {
            "news.ticker.\(ticker.uppercased())"
        }

        static let allNewsTTL: TimeInterval    = 600  // 10 min
        static let tickerNewsTTL: TimeInterval  = 600  // 10 min
    }

    // MARK: - Init

    init(
        primarySource: any MarketDataSourceProtocol,
        cache: CacheManager
    ) {
        self.primarySource = primarySource
        self.cache = cache
    }

    // MARK: - NewsRepositoryProtocol

    func fetchAllNews() async throws -> [NewsItem] {
        if let cached: [NewsItem] = await cache.get(key: CacheConfig.allNewsKey) {
            return cached
        }

        let items = try await primarySource.fetchNews()
        let sorted = items.sorted { $0.timestamp > $1.timestamp }

        await cache.set(key: CacheConfig.allNewsKey, value: sorted, ttl: CacheConfig.allNewsTTL)
        return sorted
    }

    func fetchNewsByTicker(_ ticker: String) async throws -> [NewsItem] {
        let cacheKey = CacheConfig.tickerKey(ticker)

        if let cached: [NewsItem] = await cache.get(key: cacheKey) {
            return cached
        }

        // Fetch the full news list (may come from the all-news cache),
        // then filter to the requested ticker.
        let allItems = try await fetchAllNews()

        let uppercasedTicker = ticker.uppercased()
        let filtered = allItems.filter { item in
            guard let itemTicker = item.ticker else { return false }
            return itemTicker.uppercased() == uppercasedTicker
        }

        await cache.set(key: cacheKey, value: filtered, ttl: CacheConfig.tickerNewsTTL)
        return filtered
    }
}
