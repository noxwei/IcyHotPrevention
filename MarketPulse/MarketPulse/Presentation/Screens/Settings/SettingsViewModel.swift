import Foundation
import Security

/// ViewModel for the Settings screen.
/// Manages API keys (stored in Keychain), AI provider selection, and refresh preferences.
@MainActor
@Observable
final class SettingsViewModel {

    // MARK: - API Keys

    var finvizToken: String = ""
    var finvizPortfolioId: String = ""
    var finnhubApiKey: String = ""
    var claudeApiKey: String = ""

    // MARK: - AI Provider

    var selectedAIProvider: AIProvider = .claude
    var autoRefresh: Bool = true
    var refreshMinutes: Int = 30

    enum AIProvider: String, CaseIterable, Sendable {
        case claude = "Claude API"
        case appleIntelligence = "Apple Intelligence"
    }

    // MARK: - Computed

    /// Checks at runtime whether Apple Intelligence (Foundation Models) is available.
    var isAppleIntelligenceAvailable: Bool {
        if #available(iOS 26.0, *) {
            return true
        }
        return false
    }

    /// Whether all required API keys are present for the current configuration.
    var hasRequiredKeys: Bool {
        let hasFinnhub = !finnhubApiKey.isEmpty
        let hasFinviz = !finvizToken.isEmpty && !finvizPortfolioId.isEmpty

        switch selectedAIProvider {
        case .claude:
            return hasFinnhub && hasFinviz && !claudeApiKey.isEmpty
        case .appleIntelligence:
            return hasFinnhub && hasFinviz
        }
    }

    // MARK: - Save Feedback

    var showSaveConfirmation = false

    // MARK: - Keychain Keys

    private enum KeychainKey {
        static let finvizToken = "com.marketpulse.finviz-token"
        static let finvizPortfolioId = "com.marketpulse.finviz-portfolio-id"
        static let finnhubApiKey = "com.marketpulse.finnhub-api-key"
        static let claudeApiKey = "com.marketpulse.claude-api-key"
        static let aiProvider = "com.marketpulse.ai-provider"
        static let autoRefresh = "com.marketpulse.auto-refresh"
        static let refreshMinutes = "com.marketpulse.refresh-minutes"
    }

    // MARK: - Init

    init() {
        loadFromKeychain()
    }

    // MARK: - Keychain Operations

    func loadFromKeychain() {
        finvizToken = readKeychain(key: KeychainKey.finvizToken) ?? ""
        finvizPortfolioId = readKeychain(key: KeychainKey.finvizPortfolioId) ?? ""
        finnhubApiKey = readKeychain(key: KeychainKey.finnhubApiKey) ?? ""
        claudeApiKey = readKeychain(key: KeychainKey.claudeApiKey) ?? ""

        if let providerRaw = readKeychain(key: KeychainKey.aiProvider),
           let provider = AIProvider(rawValue: providerRaw) {
            selectedAIProvider = provider
        }

        if let autoRefreshRaw = readKeychain(key: KeychainKey.autoRefresh) {
            autoRefresh = autoRefreshRaw == "true"
        }

        if let minutesRaw = readKeychain(key: KeychainKey.refreshMinutes),
           let minutes = Int(minutesRaw) {
            refreshMinutes = minutes
        }
    }

    func saveToKeychain() {
        writeKeychain(key: KeychainKey.finvizToken, value: finvizToken)
        writeKeychain(key: KeychainKey.finvizPortfolioId, value: finvizPortfolioId)
        writeKeychain(key: KeychainKey.finnhubApiKey, value: finnhubApiKey)
        writeKeychain(key: KeychainKey.claudeApiKey, value: claudeApiKey)
        writeKeychain(key: KeychainKey.aiProvider, value: selectedAIProvider.rawValue)
        writeKeychain(key: KeychainKey.autoRefresh, value: autoRefresh ? "true" : "false")
        writeKeychain(key: KeychainKey.refreshMinutes, value: String(refreshMinutes))

        showSaveConfirmation = true
    }

    // MARK: - Private Keychain Helpers

    private func readKeychain(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
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

    private func writeKeychain(key: String, value: String) {
        // Delete existing item first.
        let deleteQuery: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
        ]
        SecItemDelete(deleteQuery as CFDictionary)

        // Only write if value is non-empty.
        guard !value.isEmpty else { return }

        let addQuery: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: Data(value.utf8),
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
        ]
        SecItemAdd(addQuery as CFDictionary, nil)
    }
}
