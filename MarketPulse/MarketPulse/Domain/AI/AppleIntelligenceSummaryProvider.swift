#if canImport(FoundationModels)
import FoundationModels
#endif
import Foundation

/// AI summary provider backed by Apple's on-device Foundation Models framework.
///
/// This provider is only functional on iOS 26+ devices where Apple Intelligence
/// is available. On earlier OS versions or unsupported hardware, `isAvailable`
/// returns `false` and all generation methods throw `aiGenerationFailed`.
final class AppleIntelligenceSummaryProvider: SummaryProviderProtocol, @unchecked Sendable {

    // MARK: - SummaryProviderProtocol

    let providerName = "Apple Intelligence"

    var isAvailable: Bool {
        guard #available(iOS 26, *) else {
            return false
        }
        return checkModelAvailability()
    }

    // MARK: - SummaryProviderProtocol Methods

    func generateSummary(from scan: MarketScan) async throws -> QuickTake {
        let systemPrompt = PromptTemplates.quickTakeSystem
        let userPrompt = PromptTemplates.buildQuickTakeUserPrompt(from: scan)

        let text = try await generate(systemPrompt: systemPrompt, userPrompt: userPrompt)

        return QuickTake(
            text: text,
            provider: providerName,
            generatedAt: Date()
        )
    }

    func generateRotationNotes(
        hot: [SectorRotation],
        cold: [SectorRotation]
    ) async throws -> String {
        let systemPrompt = PromptTemplates.rotationNotesSystem
        let userPrompt = PromptTemplates.buildRotationNotesPrompt(hot: hot, cold: cold)

        return try await generate(systemPrompt: systemPrompt, userPrompt: userPrompt)
    }

    // MARK: - Private Helpers

    /// Dispatch to the appropriate implementation based on OS availability.
    private func generate(systemPrompt: String, userPrompt: String) async throws -> String {
        guard #available(iOS 26, *) else {
            throw MarketPulseError.aiGenerationFailed(
                "Apple Intelligence requires iOS 26 or later"
            )
        }

        return try await generateWithFoundationModels(
            systemPrompt: systemPrompt,
            userPrompt: userPrompt
        )
    }

    /// Check whether the on-device language model is available at runtime.
    ///
    /// This is called only when iOS 26+ is confirmed by the caller.
    @available(iOS 26, *)
    private func checkModelAvailabilityiOS26() -> Bool {
        #if canImport(FoundationModels)
        return LanguageModelSession.isAvailable
        #else
        return false
        #endif
    }

    /// Non-availability-annotated trampoline for `isAvailable`.
    private func checkModelAvailability() -> Bool {
        #if canImport(FoundationModels)
        if #available(iOS 26, *) {
            return checkModelAvailabilityiOS26()
        }
        #endif
        return false
    }

    /// Perform text generation using the Foundation Models framework.
    ///
    /// - Parameters:
    ///   - systemPrompt: The system-level instruction for the model.
    ///   - userPrompt: The user-level prompt containing scan data.
    /// - Returns: The generated text response.
    /// - Throws: `MarketPulseError.aiGenerationFailed` if generation fails.
    @available(iOS 26, *)
    private func generateWithFoundationModels(
        systemPrompt: String,
        userPrompt: String
    ) async throws -> String {
        #if canImport(FoundationModels)
        do {
            let session = LanguageModelSession {
                systemPrompt
            }
            let response = try await session.respond(to: userPrompt)
            let text = response.content

            guard !text.isEmpty else {
                throw MarketPulseError.aiGenerationFailed(
                    "Apple Intelligence returned empty response"
                )
            }

            return text
        } catch let error as MarketPulseError {
            throw error
        } catch {
            throw MarketPulseError.aiGenerationFailed(
                "Apple Intelligence generation failed: \(error.localizedDescription)"
            )
        }
        #else
        throw MarketPulseError.aiGenerationFailed(
            "FoundationModels framework is not available on this platform"
        )
        #endif
    }
}
