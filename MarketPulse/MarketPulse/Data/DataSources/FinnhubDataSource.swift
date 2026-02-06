import Foundation

// MARK: - FinnhubDataSource

/// Data source backed by the Finnhub REST API (free + premium tiers).
///
/// All methods guard on a non-empty API key and respect the injected
/// ``RateLimiter`` to stay within the upstream quota.
final class FinnhubDataSource: MarketDataSourceProtocol, @unchecked Sendable {

    let sourceIdentifier = "finnhub"

    // MARK: - Dependencies

    private let httpClient: any HTTPClientProtocol
    private let rateLimiter: RateLimiter
    private let apiKey: String
    private let baseURL = "https://finnhub.io/api/v1"

    // MARK: - Init

    init(
        httpClient: any HTTPClientProtocol,
        rateLimiter: RateLimiter,
        apiKey: String
    ) {
        self.httpClient = httpClient
        self.rateLimiter = rateLimiter
        self.apiKey = apiKey
    }

    // MARK: - MarketDataSourceProtocol

    func fetchQuotes(tickers: [String]) async throws -> [IndexSnapshot] {
        try guardAPIKey()

        return try await withThrowingTaskGroup(of: IndexSnapshot?.self) { group in
            for ticker in tickers {
                group.addTask { [self] in
                    await self.rateLimiter.acquire()

                    guard let url = URL(string: "\(self.baseURL)/quote?symbol=\(ticker)&token=\(self.apiKey)") else {
                        return nil
                    }

                    let data = try await self.httpClient.fetch(url: url, headers: [:])

                    let dto: FinnhubQuoteDTO
                    do {
                        dto = try JSONDecoder().decode(FinnhubQuoteDTO.self, from: data)
                    } catch {
                        throw MarketPulseError.jsonDecodingError(error)
                    }

                    // Finnhub returns zeroed-out responses for invalid tickers.
                    guard dto.c > 0 else { return nil }

                    return FinnhubMapper.mapQuote(dto, ticker: ticker)
                }
            }

            var snapshots: [IndexSnapshot] = []
            snapshots.reserveCapacity(tickers.count)

            for try await snapshot in group {
                if let snapshot {
                    snapshots.append(snapshot)
                }
            }

            return snapshots
        }
    }

    func fetchNews() async throws -> [NewsItem] {
        try guardAPIKey()

        await rateLimiter.acquire()

        guard let url = URL(string: "\(baseURL)/news?category=general&token=\(apiKey)") else {
            throw MarketPulseError.unexpected("Failed to construct Finnhub news URL.")
        }

        let data = try await httpClient.fetch(url: url, headers: [:])

        let dtos: [FinnhubNewsDTO]
        do {
            dtos = try JSONDecoder().decode([FinnhubNewsDTO].self, from: data)
        } catch {
            throw MarketPulseError.jsonDecodingError(error)
        }

        return dtos.map { FinnhubMapper.mapNews($0) }
    }

    func fetchTopMovers() async throws -> [MarketMover] {
        throw MarketPulseError.notSupportedBySource(sourceIdentifier)
    }

    func fetchSectorPerformance() async throws -> [SectorRotation] {
        throw MarketPulseError.notSupportedBySource(sourceIdentifier)
    }

    func fetchPortfolio() async throws -> [KeyTicker] {
        throw MarketPulseError.notSupportedBySource(sourceIdentifier)
    }

    // MARK: - Private Helpers

    /// Throws ``MarketPulseError/apiKeyMissing(_:)`` if the key is blank.
    private func guardAPIKey() throws {
        guard !apiKey.isEmpty else {
            throw MarketPulseError.apiKeyMissing("finnhub")
        }
    }
}
