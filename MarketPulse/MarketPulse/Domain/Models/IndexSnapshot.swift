import Foundation

struct IndexSnapshot: Identifiable, Codable, Sendable {
    let id: String
    let name: String
    let price: Double
    let change: Double
    let changePercent: Double
    let high: Double
    let low: Double
    let previousClose: Double

    var isPositive: Bool { change >= 0 }
}
