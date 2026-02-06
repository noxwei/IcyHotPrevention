import Foundation
import SwiftUI

enum MarketSentiment: String, Codable, CaseIterable, Sendable {
    case bullish
    case bearish
    case neutral

    var emoji: String {
        switch self {
        case .bullish: return "\u{1F7E2}"
        case .bearish: return "\u{1F534}"
        case .neutral: return "\u{26AA}"
        }
    }

    var label: String {
        switch self {
        case .bullish: return "Bullish"
        case .bearish: return "Bearish"
        case .neutral: return "Neutral"
        }
    }

    var colorName: String {
        switch self {
        case .bullish: return "gain"
        case .bearish: return "loss"
        case .neutral: return "neutral"
        }
    }
}
