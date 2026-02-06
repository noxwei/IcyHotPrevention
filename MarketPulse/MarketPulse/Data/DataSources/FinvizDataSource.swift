import Foundation

// MARK: - FinvizDataSource

/// Data source backed by the FINVIZ Elite CSV export endpoints.
///
/// Portfolio CSV data is cached in-memory for a short window so that
/// consecutive method calls within the same scan cycle avoid redundant
/// network round-trips.
final class FinvizDataSource: MarketDataSourceProtocol, @unchecked Sendable {

    let sourceIdentifier = "finviz"

    // MARK: - Dependencies

    private let httpClient: any HTTPClientProtocol
    private let authToken: String
    private let portfolioId: String

    // MARK: - Portfolio CSV Cache

    /// Lightweight in-memory cache for the portfolio CSV to avoid
    /// re-fetching within the same scan cycle. Intentionally avoids
    /// ``CacheManager`` actor overhead for this hot path.
    private var cachedPortfolioData: Data?
    private var cachedPortfolioTimestamp: Date?

    /// Portfolio cache validity window in seconds.
    private let portfolioCacheTTL: TimeInterval = 30

    // MARK: - URLs

    private var newsURL: URL {
        URL(string: "https://elite.finviz.com/news_export.ashx?v=1&auth=\(authToken)")!
    }

    private var portfolioURL: URL {
        URL(string: "https://elite.finviz.com/portfolio_export.ashx?pid=\(portfolioId)&auth=\(authToken)")!
    }

    // MARK: - Init

    init(
        httpClient: any HTTPClientProtocol,
        authToken: String,
        portfolioId: String
    ) {
        self.httpClient = httpClient
        self.authToken = authToken
        self.portfolioId = portfolioId
    }

    // MARK: - MarketDataSourceProtocol

    func fetchNews() async throws -> [NewsItem] {
        let data = try await httpClient.fetch(url: newsURL, headers: [:])
        let items: [NewsItem] = try CSVParser.parse(data: data) { row in
            guard let dto = FinvizNewsDTO(row: row) else { return nil }
            return FinvizMapper.mapNewsRow(dto)
        }
        return items
    }

    func fetchQuotes(tickers: [String]) async throws -> [IndexSnapshot] {
        let portfolioDTOs = try await fetchPortfolioDTOs()

        let requestedSet = Set(tickers.map { $0.uppercased() })

        let snapshots: [IndexSnapshot] = portfolioDTOs.compactMap { dto in
            guard requestedSet.contains(dto.ticker.uppercased()) else { return nil }
            return FinvizMapper.mapPortfolioToIndex(dto)
        }

        if snapshots.isEmpty {
            throw MarketPulseError.notSupportedBySource(sourceIdentifier)
        }

        return snapshots
    }

    func fetchTopMovers() async throws -> [MarketMover] {
        let portfolioDTOs = try await fetchPortfolioDTOs()

        let movers = portfolioDTOs
            .map { FinvizMapper.mapPortfolioToMover($0) }
            .sorted { abs($0.changePercent) > abs($1.changePercent) }

        return movers
    }

    func fetchSectorPerformance() async throws -> [SectorRotation] {
        let portfolioDTOs = try await fetchPortfolioDTOs()

        // Group DTOs by sector. Items without a sector are placed in "Other".
        var sectorBuckets: [String: [FinvizPortfolioDTO]] = [:]
        for dto in portfolioDTOs {
            let sector = dto.sector?.isEmpty == false ? dto.sector! : "Other"
            sectorBuckets[sector, default: []].append(dto)
        }

        let rotations: [SectorRotation] = sectorBuckets.map { sector, dtos in
            // Convert each DTO to a mover so we can read changePercent.
            let movers = dtos.map { FinvizMapper.mapPortfolioToMover($0) }

            // Average change percent across the sector.
            let totalChange = movers.reduce(0.0) { $0 + $1.changePercent }
            let avgChange = movers.isEmpty ? 0.0 : totalChange / Double(movers.count)

            // Leading tickers: top 2 by absolute changePercent.
            let leading = movers
                .sorted { abs($0.changePercent) > abs($1.changePercent) }
                .prefix(2)
                .map(\.ticker)

            return SectorRotation(
                id: sector,
                name: sector,
                changePercent: avgChange,
                leadingTickers: Array(leading)
            )
        }
        .sorted { abs($0.changePercent) > abs($1.changePercent) }

        return rotations
    }

    func fetchPortfolio() async throws -> [KeyTicker] {
        let portfolioDTOs = try await fetchPortfolioDTOs()
        return portfolioDTOs.map { FinvizMapper.mapPortfolioRow($0) }
    }

    // MARK: - Private Helpers

    /// Fetches and caches the raw portfolio CSV, returning parsed DTOs.
    private func fetchPortfolioDTOs() async throws -> [FinvizPortfolioDTO] {
        let data = try await fetchPortfolioData()
        let dtos: [FinvizPortfolioDTO] = try CSVParser.parse(data: data) { row in
            FinvizPortfolioDTO(row: row)
        }
        return dtos
    }

    /// Returns portfolio CSV bytes, serving from the in-memory cache when
    /// the data is still fresh.
    private func fetchPortfolioData() async throws -> Data {
        if let cached = cachedPortfolioData,
           let timestamp = cachedPortfolioTimestamp,
           Date().timeIntervalSince(timestamp) < portfolioCacheTTL {
            return cached
        }

        let data = try await httpClient.fetch(url: portfolioURL, headers: [:])
        cachedPortfolioData = data
        cachedPortfolioTimestamp = Date()
        return data
    }
}
