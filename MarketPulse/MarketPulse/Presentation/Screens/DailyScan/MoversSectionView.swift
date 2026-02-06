import SwiftUI

/// "MARKET MOVES" section showing top gainers and losers.
struct MoversSectionView: View {
    let gainers: [MarketMover]
    let losers: [MarketMover]

    var body: some View {
        VStack(alignment: .leading, spacing: MPSpacing.card) {
            SectionHeaderView(emoji: "\u{1F4C8}", title: "Market Moves")

            VStack(alignment: .leading, spacing: MPSpacing.card) {
                // Gainers
                if !gainers.isEmpty {
                    MoverGroupView(
                        label: "GAINERS",
                        labelColor: MPColor.gain,
                        movers: gainers,
                        verbPositive: "surges"
                    )
                }

                // Losers
                if !losers.isEmpty {
                    MoverGroupView(
                        label: "LOSERS",
                        labelColor: MPColor.loss,
                        movers: losers,
                        verbPositive: "tumbles"
                    )
                }
            }
            .cardStyle()
            .padding(.horizontal, MPSpacing.card)
        }
    }
}

// MARK: - Mover Group

private struct MoverGroupView: View {
    let label: String
    let labelColor: Color
    let movers: [MarketMover]
    let verbPositive: String

    var body: some View {
        VStack(alignment: .leading, spacing: MPSpacing.item) {
            Text(label)
                .font(MPFont.monoSmall())
                .foregroundStyle(labelColor)
                .tracking(2)

            ForEach(movers) { mover in
                MoverRowView(mover: mover, verb: verbPositive)
            }
        }
    }
}

// MARK: - Mover Row

private struct MoverRowView: View {
    let mover: MarketMover
    let verb: String

    var body: some View {
        HStack(alignment: .top, spacing: MPSpacing.tight) {
            Text("-")
                .font(MPFont.monoSmall())
                .foregroundStyle(MPColor.textTertiary)

            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: MPSpacing.tight) {
                    Text("$\(mover.ticker)")
                        .font(MPFont.monoMedium())
                        .foregroundStyle(MPColor.textPrimary)

                    Text(verb)
                        .font(MPFont.body())
                        .foregroundStyle(MPColor.textSecondary)

                    Text(mover.changePercent.asPercentage)
                        .font(MPFont.monoMedium())
                        .gainLossColored(value: mover.changePercent)
                }

                if let sector = mover.sector {
                    Text(sector)
                        .font(MPFont.caption())
                        .foregroundStyle(MPColor.textTertiary)
                }

                if mover.volumeRatio > 1.5 {
                    Text("Vol: \(mover.volume.asVolume) (\(String(format: "%.1fx", mover.volumeRatio)) avg)")
                        .font(MPFont.caption())
                        .foregroundStyle(MPColor.textTertiary)
                }
            }

            Spacer()

            Text(mover.price.asCurrency)
                .font(MPFont.monoSmall())
                .foregroundStyle(MPColor.textSecondary)
        }
    }
}

#Preview {
    ZStack {
        MPColor.background.ignoresSafeArea()
        ScrollView {
            MoversSectionView(
                gainers: [
                    MarketMover(id: "1", ticker: "NVDA", companyName: "NVIDIA", price: 875.30, changePercent: 5.42, volume: 45_000_000, averageVolume: 30_000_000, sector: "Technology"),
                    MarketMover(id: "2", ticker: "META", companyName: "Meta Platforms", price: 502.10, changePercent: 3.21, volume: 25_000_000, averageVolume: 20_000_000, sector: "Communication Services"),
                ],
                losers: [
                    MarketMover(id: "3", ticker: "BA", companyName: "Boeing", price: 178.45, changePercent: -4.56, volume: 18_000_000, averageVolume: 10_000_000, sector: "Industrials"),
                ]
            )
        }
    }
}
