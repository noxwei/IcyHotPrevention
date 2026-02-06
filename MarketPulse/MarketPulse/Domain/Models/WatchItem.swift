import Foundation

struct WatchItem: Identifiable, Codable, Sendable {
    let id: String
    let ticker: String
    let reason: String
}
