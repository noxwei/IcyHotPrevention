import Foundation

/// The composition root for MarketPulse.
///
/// Creates and owns all core services, data sources, repositories, and AI
/// providers. Vends pre-configured ViewModels to the SwiftUI layer.
///
/// Call ``reconfigure()`` after the user saves new API keys in Settings so
/// that data sources and AI providers are rebuilt with the latest credentials.
@MainActor
final class AppDependencyContainer: Observable {

    // MARK: - Core Services

    let httpClient: URLSessionHTTPClient
    let cache: CacheManager
    let settings: SettingsViewModel

    // MARK: - Data Sources

    private(set) var finvizSource: FinvizDataSource?
    private(set) var finnhubSource: FinnhubDataSource?

    // MARK: - Repository

    private(set) var marketRepo: MarketDataRepository

    // MARK: - AI Providers

    private(set) var claudeProvider: ClaudeAPISummaryProvider?
    private(set) var appleProvider: AppleIntelligenceSummaryProvider

    /// Returns the active AI summary provider based on the user's preference.
    /// Returns `nil` when the selected provider is not available (e.g. missing
    /// API key or unsupported device).
    var activeSummaryProvider: (any SummaryProviderProtocol)? {
        switch settings.selectedAIProvider {
        case .claude:
            return claudeProvider?.isAvailable == true ? claudeProvider : nil
        case .appleIntelligence:
            return appleProvider.isAvailable ? appleProvider : nil
        }
    }

    // MARK: - ViewModel Factory

    /// Creates a fresh ``DailyScanViewModel`` wired to the current repository
    /// and AI provider. Each access returns a new instance so SwiftUI
    /// `@State` can own the lifecycle.
    var dailyScanViewModel: DailyScanViewModel {
        let repo = marketRepo
        let provider = activeSummaryProvider
        return DailyScanViewModel {
            let useCase = GenerateDailyScanUseCase(
                marketRepo: repo,
                summaryProvider: provider
            )
            return try await useCase.execute()
        }
    }

    // MARK: - Init

    init() {
        // Core services
        self.httpClient = URLSessionHTTPClient()
        self.cache = CacheManager()
        self.settings = SettingsViewModel()

        // Apple Intelligence provider (always created; availability checked at runtime)
        self.appleProvider = AppleIntelligenceSummaryProvider()

        // Build everything else from current settings.
        // Temporary placeholder values -- overwritten immediately by `buildGraph()`.
        self.finvizSource = nil
        self.finnhubSource = nil
        self.claudeProvider = nil

        // Create a placeholder repository that will be replaced.
        // We need at least one source to satisfy the initializer, so we create
        // a temporary Finnhub source with an empty key (which will throw
        // apiKeyMissing if called before reconfigure).
        let tempLimiter = RateLimiter(maxRequestsPerMinute: 30)
        let tempSource = FinnhubDataSource(
            httpClient: httpClient,
            rateLimiter: tempLimiter,
            apiKey: ""
        )
        self.marketRepo = MarketDataRepository(
            primarySource: tempSource,
            secondarySource: nil,
            cache: cache
        )

        // Now build the real graph from stored credentials.
        buildGraph()
    }

    // MARK: - Reconfigure

    /// Rebuilds data sources, repository, and AI providers from the current
    /// ``SettingsViewModel`` state.
    ///
    /// Call this after the user saves updated API keys in Settings.
    func reconfigure() {
        buildGraph()
    }

    // MARK: - Private Graph Builder

    /// Reads credentials from ``settings`` and wires up sources + providers.
    private func buildGraph() {
        // -- Data Sources --

        // FINVIZ (primary when available)
        if !settings.finvizToken.isEmpty, !settings.finvizPortfolioId.isEmpty {
            finvizSource = FinvizDataSource(
                httpClient: httpClient,
                authToken: settings.finvizToken,
                portfolioId: settings.finvizPortfolioId
            )
        } else {
            finvizSource = nil
        }

        // Finnhub (secondary, or primary when FINVIZ is absent)
        if !settings.finnhubApiKey.isEmpty {
            let rateLimiter = RateLimiter(maxRequestsPerMinute: 30)
            finnhubSource = FinnhubDataSource(
                httpClient: httpClient,
                rateLimiter: rateLimiter,
                apiKey: settings.finnhubApiKey
            )
        } else {
            finnhubSource = nil
        }

        // -- Repository --
        // Primary = FINVIZ if available, else Finnhub.
        // Secondary = whichever is not primary, or nil.
        let primary: any MarketDataSourceProtocol
        var secondary: (any MarketDataSourceProtocol)?

        if let finviz = finvizSource {
            primary = finviz
            secondary = finnhubSource
        } else if let finnhub = finnhubSource {
            primary = finnhub
            secondary = nil
        } else {
            // No credentials at all -- use a placeholder Finnhub source that
            // will surface an apiKeyMissing error when the scan is requested.
            let emptyLimiter = RateLimiter(maxRequestsPerMinute: 30)
            primary = FinnhubDataSource(
                httpClient: httpClient,
                rateLimiter: emptyLimiter,
                apiKey: ""
            )
            secondary = nil
        }

        marketRepo = MarketDataRepository(
            primarySource: primary,
            secondarySource: secondary,
            cache: cache
        )

        // -- AI Providers --
        if !settings.claudeApiKey.isEmpty {
            claudeProvider = ClaudeAPISummaryProvider(
                httpClient: httpClient,
                apiKey: settings.claudeApiKey
            )
        } else {
            claudeProvider = nil
        }

        // appleProvider is always available (runtime check in `isAvailable`).
    }
}
