import Foundation

/// AI summary provider that calls the Anthropic Messages API directly via `URLSession`.
final class ClaudeAPISummaryProvider: SummaryProviderProtocol, @unchecked Sendable {

    // MARK: - SummaryProviderProtocol

    let providerName = "Claude API"

    var isAvailable: Bool { !apiKey.isEmpty }

    // MARK: - Private State

    private let httpClient: any HTTPClientProtocol
    private let apiKey: String
    private let model = "claude-sonnet-4-5-20250929"
    private let endpoint = URL(string: "https://api.anthropic.com/v1/messages")!

    // MARK: - Init

    /// Create a Claude API summary provider.
    ///
    /// - Parameters:
    ///   - httpClient: The HTTP client used to execute network requests.
    ///   - apiKey: The Anthropic API key. When empty, `isAvailable` returns `false`.
    init(httpClient: any HTTPClientProtocol, apiKey: String) {
        self.httpClient = httpClient
        self.apiKey = apiKey
    }

    // MARK: - SummaryProviderProtocol Methods

    func generateSummary(from scan: MarketScan) async throws -> QuickTake {
        guard isAvailable else {
            throw MarketPulseError.apiKeyMissing("Anthropic")
        }

        let systemPrompt = PromptTemplates.quickTakeSystem
        let userPrompt = PromptTemplates.buildQuickTakeUserPrompt(from: scan)

        let text = try await sendMessage(system: systemPrompt, user: userPrompt)

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
        guard isAvailable else {
            throw MarketPulseError.apiKeyMissing("Anthropic")
        }

        let systemPrompt = PromptTemplates.rotationNotesSystem
        let userPrompt = PromptTemplates.buildRotationNotesPrompt(hot: hot, cold: cold)

        return try await sendMessage(system: systemPrompt, user: userPrompt)
    }

    // MARK: - Private Helpers

    /// Send a single-turn message to the Anthropic Messages API and return the
    /// text content from the first content block.
    private func sendMessage(system: String, user: String) async throws -> String {
        let requestBody = ClaudeRequest(
            model: model,
            max_tokens: 1024,
            system: system,
            messages: [
                ClaudeMessage(role: "user", content: user)
            ]
        )

        let bodyData: Data
        do {
            let encoder = JSONEncoder()
            bodyData = try encoder.encode(requestBody)
        } catch {
            throw MarketPulseError.aiGenerationFailed(
                "Failed to encode Claude API request: \(error.localizedDescription)"
            )
        }

        let headers: [String: String] = [
            "x-api-key": apiKey,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        ]

        let responseData: Data
        do {
            responseData = try await httpClient.post(
                url: endpoint,
                headers: headers,
                body: bodyData
            )
        } catch {
            throw MarketPulseError.aiGenerationFailed(
                "Claude API request failed: \(error.localizedDescription)"
            )
        }

        let response: ClaudeResponse
        do {
            let decoder = JSONDecoder()
            response = try decoder.decode(ClaudeResponse.self, from: responseData)
        } catch {
            throw MarketPulseError.aiGenerationFailed(
                "Failed to decode Claude API response: \(error.localizedDescription)"
            )
        }

        guard let firstTextBlock = response.content.first(where: { $0.type == "text" }),
              !firstTextBlock.text.isEmpty else {
            throw MarketPulseError.aiGenerationFailed(
                "Claude API returned no text content"
            )
        }

        return firstTextBlock.text
    }
}

// MARK: - Codable Request / Response Models (File-Private)

/// Top-level request body for the Anthropic Messages API.
private struct ClaudeRequest: Encodable {
    let model: String
    let max_tokens: Int
    let system: String
    let messages: [ClaudeMessage]
}

/// A single message in the Messages API conversation.
private struct ClaudeMessage: Encodable {
    let role: String
    let content: String
}

/// Top-level response from the Anthropic Messages API.
private struct ClaudeResponse: Decodable {
    let content: [ClaudeContentBlock]
}

/// A single content block in the Messages API response.
private struct ClaudeContentBlock: Decodable {
    let type: String
    let text: String
}
