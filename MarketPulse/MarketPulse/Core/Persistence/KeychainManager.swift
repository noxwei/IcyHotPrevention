import Foundation
import Security

// MARK: - Keychain Keys

/// Well-known Keychain item identifiers for MarketPulse credentials.
enum KeychainKey: String, Sendable {
    case finvizAuthToken    = "com.marketpulse.finviz.token"
    case finvizPortfolioId  = "com.marketpulse.finviz.portfolioId"
    case finnhubApiKey      = "com.marketpulse.finnhub.apiKey"
    case claudeApiKey       = "com.marketpulse.claude.apiKey"
}

// MARK: - Keychain Manager

/// A thin wrapper around the Security framework's `SecItem*` functions for
/// storing and retrieving sensitive strings in the iOS Keychain.
///
/// All items are stored as `kSecClassGenericPassword` entries under the
/// service name `"com.marketpulse"`.
struct KeychainManager: Sendable {

    /// The Keychain service identifier shared by all MarketPulse entries.
    private static let serviceName = "com.marketpulse"

    // MARK: - Save

    /// Stores (or updates) a string value in the Keychain.
    ///
    /// - Parameters:
    ///   - key: The `KeychainKey` identifying the credential.
    ///   - value: The plaintext string to store.
    /// - Throws: `MarketPulseError.keychainError` if the operation fails.
    static func save(key: KeychainKey, value: String) throws {
        guard let data = value.data(using: .utf8) else {
            throw MarketPulseError.keychainError(
                "Unable to encode value as UTF-8 for key \(key.rawValue)."
            )
        }

        // Attempt to delete any existing item first to avoid errSecDuplicateItem.
        delete(key: key)

        let query: [String: Any] = [
            kSecClass as String:       kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: key.rawValue,
            kSecValueData as String:   data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly,
        ]

        let status = SecItemAdd(query as CFDictionary, nil)

        guard status == errSecSuccess else {
            throw MarketPulseError.keychainError(
                "Failed to save key \(key.rawValue). OSStatus: \(status)."
            )
        }
    }

    // MARK: - Load

    /// Retrieves a string value from the Keychain.
    ///
    /// - Parameter key: The `KeychainKey` identifying the credential.
    /// - Returns: The stored string, or `nil` if the item does not exist.
    static func load(key: KeychainKey) -> String? {
        let query: [String: Any] = [
            kSecClass as String:       kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: key.rawValue,
            kSecReturnData as String:  true,
            kSecMatchLimit as String:  kSecMatchLimitOne,
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess, let data = result as? Data else {
            return nil
        }

        return String(data: data, encoding: .utf8)
    }

    // MARK: - Delete

    /// Removes a value from the Keychain. No-op if the item does not exist.
    ///
    /// - Parameter key: The `KeychainKey` identifying the credential.
    @discardableResult
    static func delete(key: KeychainKey) -> Bool {
        let query: [String: Any] = [
            kSecClass as String:       kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: key.rawValue,
        ]

        let status = SecItemDelete(query as CFDictionary)
        return status == errSecSuccess || status == errSecItemNotFound
    }
}
