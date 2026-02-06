import Foundation

struct VolumeSignal: Identifiable, Codable, Sendable {
    let id: String
    let ticker: String
    let volume: Double
    let averageVolume: Double
    let changePercent: Double
    let reason: String

    var volumeRatio: Double { averageVolume > 0 ? volume / averageVolume : 0 }

    var volumeFormatted: String {
        switch volume {
        case 1_000_000_000...:
            return String(format: "%.1fB", volume / 1_000_000_000)
        case 1_000_000...:
            return String(format: "%.1fM", volume / 1_000_000)
        case 1_000...:
            return String(format: "%.1fK", volume / 1_000)
        default:
            return String(format: "%.0f", volume)
        }
    }
}
