import Foundation

/// ViewModel for the Daily Scan screen.
///
/// Uses a stored closure for scan generation to avoid importing use-case types,
/// enabling clean dependency injection from the composition root.
@MainActor
@Observable
final class DailyScanViewModel {

    // MARK: - Published State

    var scan: MarketScan?
    var isLoading = false
    var error: String?
    var lastRefreshed: Date?

    // MARK: - Dependencies

    private let generateScan: () async throws -> MarketScan

    // MARK: - Init

    /// - Parameter generateScan: An async closure that produces a `MarketScan`.
    ///   Injected by the composition root so this ViewModel has no knowledge of
    ///   use-case or repository types.
    init(generateScan: @escaping () async throws -> MarketScan) {
        self.generateScan = generateScan
    }

    // MARK: - Actions

    /// Loads the scan for the first time (shows shimmer).
    func loadScan() async {
        guard !isLoading else { return }

        isLoading = true
        error = nil

        do {
            let result = try await generateScan()
            scan = result
            lastRefreshed = Date()
            error = nil
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }

    /// Refreshes the scan (pull-to-refresh). Does not show shimmer if scan
    /// already exists; shows inline error if it fails.
    func refresh() async {
        guard !isLoading else { return }

        // Only show full shimmer if we have no data yet.
        if scan == nil {
            isLoading = true
        }

        error = nil

        do {
            let result = try await generateScan()
            scan = result
            lastRefreshed = Date()
            error = nil
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }
}
