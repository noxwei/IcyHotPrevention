import Foundation

// MARK: - Repository Protocol

/// Abstraction over the market data layer.
///
/// Defined here so the domain layer has zero framework or third-party
/// dependencies. Concrete implementations live in the Data layer.
protocol MarketDataRepositoryProtocol: Sendable {
    func fetchNews() async throws -> [NewsItem]
    func fetchIndexSnapshots() async throws -> [IndexSnapshot]
    func fetchTopMovers() async throws -> [MarketMover]
    func fetchSectorRotation() async throws -> [SectorRotation]
    func fetchPortfolio() async throws -> [KeyTicker]
}

// MARK: - Daily Scan Orchestrator

/// Orchestrates the full daily market scan pipeline:
///
/// 1. Fetches all raw data concurrently from the repository.
/// 2. Runs each analysis use case on the fetched data.
/// 3. Assembles a complete `MarketScan`.
/// 4. Optionally enriches the scan with AI-generated quick take and
///    rotation notes (failures are non-fatal).
final class GenerateDailyScanUseCase: Sendable {

    // MARK: - Dependencies

    private let marketRepo: any MarketDataRepositoryProtocol
    private let sentimentUseCase: CalculateSentimentUseCase
    private let moversUseCase: IdentifyMoversUseCase
    private let newsClassifier: ClassifyNewsUseCase
    private let sectorAnalyzer: AnalyzeSectorRotationUseCase
    private let volumeDetector: DetectVolumeSignalsUseCase
    private let watchListBuilder: BuildWatchListUseCase
    private let summaryProvider: (any SummaryProviderProtocol)?

    // MARK: - Init

    init(
        marketRepo: any MarketDataRepositoryProtocol,
        sentimentUseCase: CalculateSentimentUseCase = CalculateSentimentUseCase(),
        moversUseCase: IdentifyMoversUseCase = IdentifyMoversUseCase(),
        newsClassifier: ClassifyNewsUseCase = ClassifyNewsUseCase(),
        sectorAnalyzer: AnalyzeSectorRotationUseCase = AnalyzeSectorRotationUseCase(),
        volumeDetector: DetectVolumeSignalsUseCase = DetectVolumeSignalsUseCase(),
        watchListBuilder: BuildWatchListUseCase = BuildWatchListUseCase(),
        summaryProvider: (any SummaryProviderProtocol)? = nil
    ) {
        self.marketRepo = marketRepo
        self.sentimentUseCase = sentimentUseCase
        self.moversUseCase = moversUseCase
        self.newsClassifier = newsClassifier
        self.sectorAnalyzer = sectorAnalyzer
        self.volumeDetector = volumeDetector
        self.watchListBuilder = watchListBuilder
        self.summaryProvider = summaryProvider
    }

    // MARK: - Execute

    func execute() async throws -> MarketScan {

        // 1. Fetch all data concurrently
        async let newsTask = marketRepo.fetchNews()
        async let indexTask = marketRepo.fetchIndexSnapshots()
        async let moversTask = marketRepo.fetchTopMovers()
        async let sectorsTask = marketRepo.fetchSectorRotation()
        async let portfolioTask = marketRepo.fetchPortfolio()

        let (news, indexes, movers, sectors, portfolio) = try await (
            newsTask, indexTask, moversTask, sectorsTask, portfolioTask
        )

        // 2. Process through each use case
        let sentiment = sentimentUseCase.calculate(from: indexes)
        let (gainers, losers) = moversUseCase.identify(from: movers)
        let (corporateNews, macroNews) = newsClassifier.classify(news)
        let (hotSectors, coldSectors, analyzerNotes) = sectorAnalyzer.analyze(sectors)
        let volumeSignals = volumeDetector.detect(from: movers)
        let allNews = corporateNews + macroNews
        let watchList = watchListBuilder.build(
            movers: movers,
            news: allNews,
            volumeSignals: volumeSignals
        )

        // 3. Build the initial scan (no quick take yet)
        var rotationNotes = analyzerNotes

        // 4. If summaryProvider is available, try to generate enhanced rotation notes
        //    (non-fatal -- fall back to the analyzer's rule-based notes)
        if let provider = summaryProvider {
            do {
                rotationNotes = try await provider.generateRotationNotes(
                    hot: hotSectors,
                    cold: coldSectors
                )
            } catch {
                // Keep analyzerNotes as fallback -- already assigned above
            }
        }

        let scan = MarketScan(
            id: UUID(),
            generatedAt: Date(),
            sentiment: sentiment,
            indexSnapshots: indexes,
            topGainers: gainers,
            topLosers: losers,
            corporateNews: corporateNews,
            macroNews: macroNews,
            hotSectors: hotSectors,
            coldSectors: coldSectors,
            rotationNotes: rotationNotes,
            volumeSignals: volumeSignals,
            keyTickers: portfolio,
            quickTake: nil,
            watchList: watchList
        )

        // 5. If summaryProvider is available, try to generate quick take
        //    (non-fatal -- the scan is still useful without it)
        guard let provider = summaryProvider else { return scan }

        do {
            let quickTake = try await provider.generateSummary(from: scan)
            return scan.withQuickTake(quickTake)
        } catch {
            return scan
        }
    }
}
