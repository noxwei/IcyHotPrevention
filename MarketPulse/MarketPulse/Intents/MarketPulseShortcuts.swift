import AppIntents
import Foundation

/// Siri Shortcuts intent that runs a full daily market scan and returns a
/// plain-text summary suitable for voice or Shortcuts display.
///
/// For speed, the scan runs without an AI summary provider so only
/// rule-based analysis is included.
struct DailyScanIntent: AppIntent {

    static var title: LocalizedStringResource = "Get Market Pulse"
    static var description: IntentDescription = IntentDescription(
        "Get today's market scan summary",
        categoryName: "Market Data"
    )

    // MARK: - Perform

    func perform() async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog {
        do {
            let scan = try await generateScan()
            let summary = formatScanSummary(scan)
            return .result(value: summary, dialog: "\(summary)")
        } catch {
            let message = "Unable to generate market scan: \(error.localizedDescription)"
            return .result(value: message, dialog: "\(message)")
        }
    }

    // MARK: - Scan Generation

    /// Builds the data pipeline and runs ``GenerateDailyScanUseCase`` without
    /// an AI provider for minimal latency.
    private func generateScan() async throws -> MarketScan {
        let httpClient = URLSessionHTTPClient()
        let cache = CacheManager(subdirectory: "MarketPulseIntents")

        // Load credentials from Keychain.
        let finvizToken = loadKeychainValue(account: KeychainAccounts.finvizToken)
        let finvizPortfolioId = loadKeychainValue(account: KeychainAccounts.finvizPortfolioId)
        let finnhubKey = loadKeychainValue(account: KeychainAccounts.finnhubApiKey)

        // Build data sources.
        var primarySource: (any MarketDataSourceProtocol)?
        var secondarySource: (any MarketDataSourceProtocol)?

        if let token = finvizToken, let pid = finvizPortfolioId,
           !token.isEmpty, !pid.isEmpty {
            primarySource = FinvizDataSource(
                httpClient: httpClient,
                authToken: token,
                portfolioId: pid
            )
        }

        if let key = finnhubKey, !key.isEmpty {
            let rateLimiter = RateLimiter(maxRequestsPerMinute: 30)
            let source = FinnhubDataSource(
                httpClient: httpClient,
                rateLimiter: rateLimiter,
                apiKey: key
            )
            if primarySource == nil {
                primarySource = source
            } else {
                secondarySource = source
            }
        }

        guard let primary = primarySource else {
            throw MarketPulseError.apiKeyMissing(
                "No data source credentials configured. Open MarketPulse Settings to add API keys."
            )
        }

        let repo = MarketDataRepository(
            primarySource: primary,
            secondarySource: secondarySource,
            cache: cache
        )

        // Run without AI provider for speed.
        let useCase = GenerateDailyScanUseCase(
            marketRepo: repo,
            summaryProvider: nil
        )

        return try await useCase.execute()
    }

    // MARK: - Text Formatting

    /// Converts a ``MarketScan`` into a concise plain-text summary.
    private func formatScanSummary(_ scan: MarketScan) -> String {
        var lines: [String] = []

        // Header
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        let dateStr = formatter.string(from: scan.generatedAt)
        lines.append("MarketPulse - \(dateStr)")
        lines.append("Sentiment: \(scan.sentiment.label)")
        lines.append("")

        // Index Snapshots
        if !scan.indexSnapshots.isEmpty {
            lines.append("-- Indexes --")
            for idx in scan.indexSnapshots {
                let sign = idx.change >= 0 ? "+" : ""
                let priceStr = String(format: "%.2f", idx.price)
                let changeStr = String(format: "%.2f", idx.changePercent)
                lines.append("\(idx.name): \(priceStr) (\(sign)\(changeStr)%)")
            }
            lines.append("")
        }

        // Top Gainers
        if !scan.topGainers.isEmpty {
            lines.append("-- Top Gainers --")
            for mover in scan.topGainers.prefix(5) {
                let changeStr = String(format: "+%.2f%%", mover.changePercent)
                lines.append("\(mover.ticker): \(changeStr)")
            }
            lines.append("")
        }

        // Top Losers
        if !scan.topLosers.isEmpty {
            lines.append("-- Top Losers --")
            for mover in scan.topLosers.prefix(5) {
                let changeStr = String(format: "%.2f%%", mover.changePercent)
                lines.append("\(mover.ticker): \(changeStr)")
            }
            lines.append("")
        }

        // Hot Sectors
        if !scan.hotSectors.isEmpty {
            lines.append("-- Hot Sectors --")
            for sector in scan.hotSectors.prefix(3) {
                let changeStr = String(format: "+%.2f%%", sector.changePercent)
                let tickers = sector.leadingTickers.joined(separator: ", ")
                lines.append("\(sector.name) \(changeStr) [\(tickers)]")
            }
            lines.append("")
        }

        // Cold Sectors
        if !scan.coldSectors.isEmpty {
            lines.append("-- Cold Sectors --")
            for sector in scan.coldSectors.prefix(3) {
                let changeStr = String(format: "%.2f%%", sector.changePercent)
                let tickers = sector.leadingTickers.joined(separator: ", ")
                lines.append("\(sector.name) \(changeStr) [\(tickers)]")
            }
            lines.append("")
        }

        // Volume Signals
        if !scan.volumeSignals.isEmpty {
            lines.append("-- Volume Signals --")
            for signal in scan.volumeSignals.prefix(5) {
                let ratioStr = String(format: "%.1fx", signal.volumeRatio)
                lines.append("\(signal.ticker) \(ratioStr) avg vol - \(signal.reason)")
            }
            lines.append("")
        }

        // Watch List
        if !scan.watchList.isEmpty {
            lines.append("-- Watch List --")
            for item in scan.watchList.prefix(5) {
                lines.append("\(item.ticker): \(item.reason)")
            }
        }

        return lines.joined(separator: "\n")
    }

    // MARK: - Keychain Helpers

    /// Keychain account identifiers matching those used by ``SettingsViewModel``.
    private enum KeychainAccounts {
        static let finnhubApiKey = "com.marketpulse.finnhub-api-key"
        static let finvizToken = "com.marketpulse.finviz-token"
        static let finvizPortfolioId = "com.marketpulse.finviz-portfolio-id"
    }

    /// Reads a single string value from the Keychain by account name.
    private func loadKeychainValue(account: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: account,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess,
              let data = result as? Data,
              let value = String(data: data, encoding: .utf8) else {
            return nil
        }

        return value
    }
}
