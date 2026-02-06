import Foundation

/// Abstraction for AI-powered summary generation.
///
/// Conforming types provide one of two backends:
///   - Claude API (via Anthropic Messages API)
///   - Apple Intelligence (via Foundation Models framework, iOS 26+)
protocol SummaryProviderProtocol: Sendable {

    /// Human-readable name of the AI provider (e.g. "Claude API", "Apple Intelligence").
    var providerName: String { get }

    /// Whether this provider is currently available for use.
    ///
    /// Returns `false` when a required API key is missing (Claude) or when the
    /// device/OS does not support on-device Foundation Models (Apple Intelligence).
    var isAvailable: Bool { get }

    /// Generate a `QuickTake` analysis paragraph from a completed `MarketScan`.
    ///
    /// - Parameter scan: The fully populated scan to summarize.
    /// - Returns: A `QuickTake` containing the AI-generated summary text.
    /// - Throws: `MarketPulseError.aiGenerationFailed` on failure.
    func generateSummary(from scan: MarketScan) async throws -> QuickTake

    /// Generate human-readable rotation notes for the given hot and cold sectors.
    ///
    /// - Parameters:
    ///   - hot: Sectors exhibiting positive rotation (gaining momentum).
    ///   - cold: Sectors exhibiting negative rotation (losing momentum).
    /// - Returns: A plain-text rotation analysis string.
    /// - Throws: `MarketPulseError.aiGenerationFailed` on failure.
    func generateRotationNotes(hot: [SectorRotation], cold: [SectorRotation]) async throws -> String
}
