import SwiftUI

/// "SECTOR ROTATION" section with hot/cold bars and rotation notes.
struct SectorsSectionView: View {
    let hotSectors: [SectorRotation]
    let coldSectors: [SectorRotation]
    let rotationNotes: String

    var body: some View {
        VStack(alignment: .leading, spacing: MPSpacing.card) {
            SectionHeaderView(emoji: "\u{1F4CA}", title: "Sector Rotation")

            VStack(alignment: .leading, spacing: MPSpacing.card) {
                // Hot sectors
                if !hotSectors.isEmpty {
                    VStack(alignment: .leading, spacing: MPSpacing.item) {
                        Text("\u{1F525} HOT:")
                            .font(MPFont.monoSmall())
                            .foregroundStyle(MPColor.hotSector)
                            .tracking(1)

                        ForEach(hotSectors) { sector in
                            SectorBarView(
                                name: sector.name,
                                changePercent: sector.changePercent,
                                leadingTickers: sector.leadingTickers
                            )
                        }
                    }
                }

                // Cold sectors
                if !coldSectors.isEmpty {
                    VStack(alignment: .leading, spacing: MPSpacing.item) {
                        Text("\u{2744}\u{FE0F} COLD:")
                            .font(MPFont.monoSmall())
                            .foregroundStyle(MPColor.coldSector)
                            .tracking(1)

                        ForEach(coldSectors) { sector in
                            SectorBarView(
                                name: sector.name,
                                changePercent: sector.changePercent,
                                leadingTickers: sector.leadingTickers
                            )
                        }
                    }
                }

                // Rotation notes
                if !rotationNotes.isEmpty {
                    SectionDivider()

                    VStack(alignment: .leading, spacing: MPSpacing.item) {
                        Text("\u{1F4CC} ROTATION NOTES:")
                            .font(MPFont.monoSmall())
                            .foregroundStyle(MPColor.textSecondary)
                            .tracking(1)

                        Text(rotationNotes)
                            .font(MPFont.body())
                            .foregroundStyle(MPColor.textSecondary)
                            .lineSpacing(4)
                    }
                }
            }
            .cardStyle()
            .padding(.horizontal, MPSpacing.card)
        }
    }
}

#Preview {
    ZStack {
        MPColor.background.ignoresSafeArea()
        ScrollView {
            SectorsSectionView(
                hotSectors: [
                    SectorRotation(id: "tech", name: "Technology", changePercent: 3.45, leadingTickers: ["AAPL", "MSFT", "NVDA"]),
                    SectorRotation(id: "health", name: "Healthcare", changePercent: 2.10, leadingTickers: ["UNH", "JNJ"]),
                ],
                coldSectors: [
                    SectorRotation(id: "energy", name: "Energy", changePercent: -2.80, leadingTickers: ["XOM", "CVX"]),
                    SectorRotation(id: "real", name: "Real Estate", changePercent: -1.90, leadingTickers: ["AMT"]),
                ],
                rotationNotes: "Money rotating out of energy and real estate into tech and healthcare. Defensive positioning suggests caution despite bullish headline sentiment."
            )
        }
    }
}
