import Foundation

struct KeyTicker: Identifiable, Codable, Sendable {
    let id: String
    let ticker: String
    let price: Double
    let changePercent: Double
    let note: String?

    var isPositive: Bool { changePercent >= 0 }
}
