import SwiftUI

/// Horizontal bar showing sector name + percentage.
/// Bar extends right (hot/green-orange) or left (cold/blue) from center.
struct SectorBarView: View {
    let name: String
    let changePercent: Double
    let leadingTickers: [String]

    /// Maximum absolute percent the bar can represent (for scaling).
    private let maxPercent: Double = 10.0

    private var barColor: Color {
        changePercent >= 0 ? MPColor.hotSector : MPColor.coldSector
    }

    private var barFraction: CGFloat {
        let clamped = min(abs(changePercent), maxPercent)
        return CGFloat(clamped / maxPercent)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: MPSpacing.tight) {
            HStack {
                Text(name)
                    .font(MPFont.monoSmall())
                    .foregroundStyle(MPColor.textPrimary)
                    .frame(width: 100, alignment: .leading)

                GeometryReader { geometry in
                    let fullWidth = geometry.size.width
                    let barWidth = fullWidth * barFraction

                    ZStack(alignment: changePercent >= 0 ? .leading : .trailing) {
                        // Track
                        Rectangle()
                            .fill(MPColor.surface)
                            .frame(height: 14)
                            .clipShape(RoundedRectangle(cornerRadius: 3))

                        // Filled bar
                        Rectangle()
                            .fill(barColor.opacity(0.8))
                            .frame(width: max(barWidth, 2), height: 14)
                            .clipShape(RoundedRectangle(cornerRadius: 3))
                    }
                }
                .frame(height: 14)

                Text(String(format: "%+.2f%%", changePercent))
                    .font(MPFont.monoSmall())
                    .gainLossColored(value: changePercent)
                    .frame(width: 70, alignment: .trailing)
            }

            if !leadingTickers.isEmpty {
                Text(leadingTickers.map { "$\($0)" }.joined(separator: " "))
                    .font(MPFont.caption())
                    .foregroundStyle(MPColor.textTertiary)
                    .padding(.leading, 100)
            }
        }
    }
}

#Preview {
    ZStack {
        MPColor.background.ignoresSafeArea()
        VStack(spacing: MPSpacing.item) {
            SectorBarView(
                name: "Technology",
                changePercent: 3.45,
                leadingTickers: ["AAPL", "MSFT", "NVDA"]
            )
            SectorBarView(
                name: "Energy",
                changePercent: -2.18,
                leadingTickers: ["XOM", "CVX"]
            )
            SectorBarView(
                name: "Financials",
                changePercent: 0.82,
                leadingTickers: ["JPM"]
            )
        }
        .padding()
    }
}
