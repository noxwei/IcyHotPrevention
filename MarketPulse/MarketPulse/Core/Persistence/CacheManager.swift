import Foundation

/// A hybrid memory + disk cache with per-entry TTL expiration.
///
/// Memory entries are checked first for fast reads. Disk entries live in the
/// app's Caches directory under `MarketPulse/` and survive app restarts
/// (but may be purged by the OS under storage pressure).
///
/// All access is serialized through the actor to guarantee thread safety.
actor CacheManager {

    // MARK: - Types

    /// Wraps a cached value together with its expiration date.
    private struct CacheEntry: Codable {
        let data: Data
        let expiresAt: Date
    }

    // MARK: - Storage

    /// In-memory cache keyed by caller-supplied string keys.
    private var memoryCache: [String: CacheEntry] = [:]

    /// Root directory for disk-backed cache files.
    private let diskCacheURL: URL

    // MARK: - Init

    /// Creates a cache manager.
    ///
    /// - Parameter subdirectory: Folder name inside the system Caches directory.
    ///   Defaults to `"MarketPulse"`.
    init(subdirectory: String = "MarketPulse") {
        let caches = FileManager.default.urls(
            for: .cachesDirectory,
            in: .userDomainMask
        ).first!

        self.diskCacheURL = caches.appendingPathComponent(subdirectory, isDirectory: true)

        // Ensure the cache directory exists.
        try? FileManager.default.createDirectory(
            at: diskCacheURL,
            withIntermediateDirectories: true
        )
    }

    // MARK: - Public API

    /// Retrieves a value from the cache if it exists and has not expired.
    ///
    /// Checks memory first, then falls back to disk. Expired entries are
    /// removed lazily on access.
    ///
    /// - Parameter key: The cache key.
    /// - Returns: The decoded value, or `nil` if not found / expired / corrupt.
    func get<T: Codable>(key: String) -> T? {
        // 1. Check memory.
        if let entry = memoryCache[key] {
            if entry.expiresAt > Date() {
                return decode(entry.data)
            }
            // Expired -- remove lazily.
            memoryCache.removeValue(forKey: key)
            removeDiskEntry(for: key)
            return nil
        }

        // 2. Check disk.
        let fileURL = diskURL(for: key)
        guard let fileData = try? Data(contentsOf: fileURL) else { return nil }
        guard let entry = try? JSONDecoder().decode(CacheEntry.self, from: fileData) else {
            // Corrupt file -- clean up.
            removeDiskEntry(for: key)
            return nil
        }

        guard entry.expiresAt > Date() else {
            removeDiskEntry(for: key)
            return nil
        }

        // Promote to memory for faster subsequent reads.
        memoryCache[key] = entry
        return decode(entry.data)
    }

    /// Stores a value in both memory and disk caches with the given TTL.
    ///
    /// - Parameters:
    ///   - key: The cache key.
    ///   - value: The `Codable` value to store.
    ///   - ttl: Time-to-live in seconds from now.
    func set<T: Codable>(key: String, value: T, ttl: TimeInterval) {
        guard let encoded = try? JSONEncoder().encode(value) else { return }

        let entry = CacheEntry(
            data: encoded,
            expiresAt: Date().addingTimeInterval(ttl)
        )

        // Memory.
        memoryCache[key] = entry

        // Disk.
        if let entryData = try? JSONEncoder().encode(entry) {
            let fileURL = diskURL(for: key)
            try? entryData.write(to: fileURL, options: .atomic)
        }
    }

    /// Removes a single entry from both memory and disk.
    ///
    /// - Parameter key: The cache key to invalidate.
    func invalidate(key: String) {
        memoryCache.removeValue(forKey: key)
        removeDiskEntry(for: key)
    }

    /// Removes all cached entries from both memory and disk.
    func clearAll() {
        memoryCache.removeAll()

        if let files = try? FileManager.default.contentsOfDirectory(
            at: diskCacheURL,
            includingPropertiesForKeys: nil
        ) {
            for file in files {
                try? FileManager.default.removeItem(at: file)
            }
        }
    }

    // MARK: - Private Helpers

    /// Returns the disk URL for a given cache key, using a safe file name.
    private func diskURL(for key: String) -> URL {
        let safeName = key
            .addingPercentEncoding(withAllowedCharacters: .alphanumerics) ?? key
        return diskCacheURL.appendingPathComponent(safeName + ".cache")
    }

    /// Removes the disk file for a given cache key, ignoring errors.
    private func removeDiskEntry(for key: String) {
        let fileURL = diskURL(for: key)
        try? FileManager.default.removeItem(at: fileURL)
    }

    /// Decodes data into the requested `Codable` type, returning `nil` on failure.
    private func decode<T: Codable>(_ data: Data) -> T? {
        try? JSONDecoder().decode(T.self, from: data)
    }
}
