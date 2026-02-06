import Foundation

struct SectorRotation: Identifiable, Codable, Sendable {
    let id: String
    let name: String
    let changePercent: Double
    let leadingTickers: [String]

    var isHot: Bool { changePercent > 0 }

    var designation: Designation {
        if changePercent > 1.5 {
            return .hot
        } else if changePercent < -1.5 {
            return .cold
        } else {
            return .neutral
        }
    }

    enum Designation: String, Codable, Sendable {
        case hot
        case cold
        case neutral
    }
}
