import Foundation

struct QuickTake: Codable, Sendable {
    let text: String
    let provider: String
    let generatedAt: Date
}
