import SwiftUI

// MARK: - Colors

enum MPColor {
    static let background = Color(red: 0.07, green: 0.07, blue: 0.10)
    static let cardBackground = Color(red: 0.11, green: 0.11, blue: 0.15)
    static let surface = Color(red: 0.15, green: 0.15, blue: 0.19)
    static let textPrimary = Color.white
    static let textSecondary = Color(white: 0.6)
    static let textTertiary = Color(white: 0.4)
    static let gain = Color(red: 0.0, green: 0.85, blue: 0.4)
    static let loss = Color(red: 1.0, green: 0.25, blue: 0.25)
    static let neutral = Color(white: 0.5)
    static let accent = Color(red: 0.2, green: 0.6, blue: 1.0)
    static let divider = Color(white: 0.2)
    static let hotSector = Color(red: 1.0, green: 0.5, blue: 0.0)
    static let coldSector = Color(red: 0.3, green: 0.6, blue: 1.0)

    /// Returns the appropriate gain/loss/neutral color for a numeric value.
    static func forValue(_ value: Double) -> Color {
        if value > 0 { return gain }
        if value < 0 { return loss }
        return neutral
    }
}

// MARK: - Typography

enum MPFont {
    static func monoLarge() -> Font {
        .system(size: 18, design: .monospaced).weight(.semibold)
    }

    static func monoMedium() -> Font {
        .system(size: 14, design: .monospaced).weight(.medium)
    }

    static func monoSmall() -> Font {
        .system(size: 12, design: .monospaced).weight(.regular)
    }

    static func headerLarge() -> Font {
        .system(size: 24, design: .default).weight(.heavy)
    }

    static func sectionTitle() -> Font {
        .system(size: 16, design: .default).weight(.bold)
    }

    static func body() -> Font {
        .system(size: 14, design: .default).weight(.regular)
    }

    static func caption() -> Font {
        .system(size: 11, design: .default).weight(.regular)
    }
}

// MARK: - Spacing

enum MPSpacing {
    static let section: CGFloat = 24
    static let card: CGFloat = 16
    static let item: CGFloat = 8
    static let tight: CGFloat = 4
}

// MARK: - Corner Radius

enum MPRadius {
    static let card: CGFloat = 12
    static let badge: CGFloat = 8
    static let chip: CGFloat = 6
}
