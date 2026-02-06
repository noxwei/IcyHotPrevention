import SwiftUI

// MARK: - Gain/Loss Color Modifier

struct GainLossStyle: ViewModifier {
    let value: Double

    func body(content: Content) -> some View {
        content
            .foregroundStyle(MPColor.forValue(value))
    }
}

extension View {
    /// Colors text green for positive values, red for negative, gray for zero.
    func gainLossColored(value: Double) -> some View {
        modifier(GainLossStyle(value: value))
    }
}

// MARK: - Monospace Number Modifier

struct MonospaceNumberStyle: ViewModifier {
    let size: CGFloat

    func body(content: Content) -> some View {
        content
            .font(.system(size: size, design: .monospaced).weight(.medium))
            .monospacedDigit()
    }
}

extension View {
    /// Applies monospaced digit styling at the given size.
    func monoNumber(size: CGFloat = 14) -> some View {
        modifier(MonospaceNumberStyle(size: size))
    }
}

// MARK: - Card Background Modifier

struct CardStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(MPSpacing.card)
            .background(MPColor.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: MPRadius.card))
    }
}

extension View {
    /// Wraps content in a dark card with rounded corners.
    func cardStyle() -> some View {
        modifier(CardStyle())
    }
}

// MARK: - Section Divider

struct SectionDivider: View {
    var body: some View {
        Rectangle()
            .fill(MPColor.divider)
            .frame(height: 1)
            .padding(.horizontal, MPSpacing.card)
    }
}
