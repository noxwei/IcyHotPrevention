import SwiftUI

/// Sentiment badge on top, then HStack of 3 IndexCardViews (SPY/QQQ/DIA).
struct SentimentSectionView: View {
    let sentiment: MarketSentiment
    let indexSnapshots: [IndexSnapshot]

    var body: some View {
        VStack(spacing: MPSpacing.card) {
            // Sentiment badge
            SentimentBadgeView(sentiment: sentiment)
                .padding(.bottom, MPSpacing.item)

            // Index cards row
            HStack(spacing: MPSpacing.item) {
                ForEach(indexSnapshots) { snapshot in
                    IndexCardView(snapshot: snapshot)
                }
            }
            .padding(.horizontal, MPSpacing.card)
        }
    }
}

// MARK: - Index Card

/// A single index card showing ticker, price, and change percentage.
private struct IndexCardView: View {
    let snapshot: IndexSnapshot

    var body: some View {
        VStack(spacing: MPSpacing.tight) {
            // Ticker name
            Text(snapshot.name)
                .font(MPFont.monoSmall())
                .foregroundStyle(MPColor.textSecondary)
                .tracking(1)

            // Price
            Text(snapshot.price.asCurrency)
                .font(MPFont.monoLarge())
                .foregroundStyle(MPColor.textPrimary)
                .lineLimit(1)
                .minimumScaleFactor(0.7)

            // Change percentage
            Text(snapshot.changePercent.asPercentage)
                .font(MPFont.monoMedium())
                .gainLossColored(value: snapshot.changePercent)

            // Day range
            HStack(spacing: 2) {
                Text("L:")
                    .font(MPFont.caption())
                    .foregroundStyle(MPColor.textTertiary)
                Text(snapshot.low.asCurrency)
                    .font(MPFont.caption())
                    .foregroundStyle(MPColor.textTertiary)
            }
            .lineLimit(1)
            .minimumScaleFactor(0.7)

            HStack(spacing: 2) {
                Text("H:")
                    .font(MPFont.caption())
                    .foregroundStyle(MPColor.textTertiary)
                Text(snapshot.high.asCurrency)
                    .font(MPFont.caption())
                    .foregroundStyle(MPColor.textTertiary)
            }
            .lineLimit(1)
            .minimumScaleFactor(0.7)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, MPSpacing.card)
        .padding(.horizontal, MPSpacing.item)
        .background(MPColor.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: MPRadius.card))
        .overlay(
            RoundedRectangle(cornerRadius: MPRadius.card)
                .strokeBorder(MPColor.divider, lineWidth: 1)
        )
    }
}

#Preview {
    ZStack {
        MPColor.background.ignoresSafeArea()
        SentimentSectionView(
            sentiment: .bullish,
            indexSnapshots: [
                IndexSnapshot(id: "SPY", name: "SPY", price: 502.34, change: 4.56, changePercent: 0.92, high: 505.10, low: 498.20, previousClose: 497.78),
                IndexSnapshot(id: "QQQ", name: "QQQ", price: 432.10, change: -2.30, changePercent: -0.53, high: 435.00, low: 430.50, previousClose: 434.40),
                IndexSnapshot(id: "DIA", name: "DIA", price: 389.55, change: 1.23, changePercent: 0.32, high: 391.00, low: 387.00, previousClose: 388.32),
            ]
        )
    }
}
