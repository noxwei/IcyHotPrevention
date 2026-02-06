import AppIntents
import Foundation

/// Siri Shortcuts intent that looks up a single stock ticker and returns
/// its current price with daily change.
///
/// Resolution order:
/// 1. Finnhub REST API (if an API key is stored in the Keychain).
/// 2. FINVIZ portfolio CSV (if auth token + portfolio ID are stored).
/// 3. Descriptive error message.
struct TickerLookupIntent: AppIntent {

    static var title: LocalizedStringResource = "Look Up Stock Ticker"
    static var description: IntentDescription = IntentDescription(
        "Get the current price and change for a stock ticker",
        categoryName: "Market Data"
    )

    @Parameter(title: "Ticker Symbol", description: "Stock ticker like AAPL, TSLA, SPY")
    var ticker: String

    static var parameterSummary: some ParameterSummary {
        Summary("Look up \(\.$ticker)")
    }

    // MARK: - Perform

    func perform() async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog {
        let normalizedTicker = ticker
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .uppercased()

        guard !normalizedTicker.isEmpty else {
            return .result(
                value: "Please provide a ticker symbol.",
                dialog: "Please provide a ticker symbol."
            )
        }

        // --- Attempt 1: Finnhub ---
        if let finnhubKey = loadKeychainValue(account: KeychainAccounts.finnhubApiKey),
           !finnhubKey.isEmpty {
            do {
                let result = try await fetchFromFinnhub(
                    ticker: normalizedTicker,
                    apiKey: finnhubKey
                )
                return .result(value: result, dialog: "\(result)")
            } catch {
                // Fall through to FINVIZ attempt.
            }
        }

        // --- Attempt 2: FINVIZ portfolio CSV ---
        if let token = loadKeychainValue(account: KeychainAccounts.finvizToken),
           let portfolioId = loadKeychainValue(account: KeychainAccounts.finvizPortfolioId),
           !token.isEmpty, !portfolioId.isEmpty {
            do {
                let result = try await fetchFromFinviz(
                    ticker: normalizedTicker,
                    authToken: token,
                    portfolioId: portfolioId
                )
                return .result(value: result, dialog: "\(result)")
            } catch {
                return .result(
                    value: "Could not find \(normalizedTicker) in your FINVIZ portfolio.",
                    dialog: "Could not find \(normalizedTicker) in your FINVIZ portfolio."
                )
            }
        }

        // --- No data sources configured ---
        let message = "No API keys configured. Open MarketPulse Settings to add your Finnhub or FINVIZ credentials."
        return .result(value: message, dialog: "\(message)")
    }

    // MARK: - Finnhub Fetch

    /// Fetches a single-ticker quote from the Finnhub REST API.
    private func fetchFromFinnhub(ticker: String, apiKey: String) async throws -> String {
        let httpClient = URLSessionHTTPClient()
        let rateLimiter = RateLimiter(maxRequestsPerMinute: 30)

        await rateLimiter.acquire()

        guard let url = URL(
            string: "https://finnhub.io/api/v1/quote?symbol=\(ticker)&token=\(apiKey)"
        ) else {
            throw MarketPulseError.unexpected("Invalid Finnhub URL for ticker \(ticker).")
        }

        let data = try await httpClient.fetch(url: url, headers: [:])
        let dto = try JSONDecoder().decode(FinnhubQuoteDTO.self, from: data)

        // Finnhub returns zeroed-out responses for invalid tickers.
        guard dto.c > 0 else {
            throw MarketPulseError.unexpected("No quote data for \(ticker).")
        }

        return formatQuote(ticker: ticker, price: dto.c, changePercent: dto.dp)
    }

    // MARK: - FINVIZ Fetch

    /// Fetches the FINVIZ portfolio CSV and locates the requested ticker.
    private func fetchFromFinviz(
        ticker: String,
        authToken: String,
        portfolioId: String
    ) async throws -> String {
        let httpClient = URLSessionHTTPClient()

        guard let url = URL(
            string: "https://elite.finviz.com/portfolio_export.ashx?pid=\(portfolioId)&auth=\(authToken)"
        ) else {
            throw MarketPulseError.unexpected("Invalid FINVIZ portfolio URL.")
        }

        let data = try await httpClient.fetch(url: url, headers: [:])
        let dtos: [FinvizPortfolioDTO] = try CSVParser.parse(data: data) { row in
            FinvizPortfolioDTO(row: row)
        }

        guard let match = dtos.first(where: { $0.ticker.uppercased() == ticker }) else {
            throw MarketPulseError.unexpected("Ticker \(ticker) not found in portfolio.")
        }

        let price = Double(match.price.replacingOccurrences(of: ",", with: "")) ?? 0
        let changeStr = match.change
            .replacingOccurrences(of: "%", with: "")
            .replacingOccurrences(of: ",", with: "")
        let changePercent = Double(changeStr) ?? 0

        return formatQuote(ticker: ticker, price: price, changePercent: changePercent)
    }

    // MARK: - Formatting

    /// Formats a quote into a user-friendly string: `$AAPL 185.50 (+1.23%)`
    private func formatQuote(ticker: String, price: Double, changePercent: Double) -> String {
        let sign = changePercent >= 0 ? "+" : ""
        let priceStr = String(format: "%.2f", price)
        let changeStr = String(format: "%.2f", changePercent)
        return "$\(ticker) \(priceStr) (\(sign)\(changeStr)%)"
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
