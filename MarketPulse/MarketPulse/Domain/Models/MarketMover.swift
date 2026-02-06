import Foundation

struct MarketMover: Identifiable, Codable, Sendable {
    let id: String
    let ticker: String
    let companyName: String
    let price: Double
    let changePercent: Double
    let volume: Double
    let averageVolume: Double
    let sector: String?

    var isGainer: Bool { changePercent > 0 }
    var volumeRatio: Double { averageVolume > 0 ? volume / averageVolume : 0 }
}
