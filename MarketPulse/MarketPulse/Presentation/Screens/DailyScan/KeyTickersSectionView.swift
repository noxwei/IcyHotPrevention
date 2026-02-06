import SwiftUI

/// "KEY TICKERS" section with a 2-column grid of ticker cards.
struct KeyTickersSectionView: View {
    let tickers: [KeyTicker]

    private let columns = [
        GridItem(.flexible(), spacing: MPSpacing.item),
        GridItem(.flexible(), spacing: MPSpacing.item),
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: MPSpacing.card) {
            SectionHeaderView(emoji: "\u{1F4A1}", title: "Key Tickers")

            LazyVGrid(columns: columns, spacing: MPSpacing.item) {
                ForEach(tickers) { ticker in
                    KeyTickerCardView(ticker: ticker)
                }
            }
            .padding(.horizontal, MPSpacing.card)
        }
    }
}

// MARK: - Key Ticker Card

private struct KeyTickerCardView: View {
    let ticker: KeyTicker

    var body: some View {
        VStack(spacing: MPSpacing.tight) {
            // Ticker symbol
            Text("$\(ticker.ticker)")
                .font(MPFont.monoMedium())
                .foregroundStyle(MPColor.textPrimary)

            // Price
            Text(ticker.price.asCurrency)
                .font(MPFont.monoLarge())
                .foregroundStyle(MPColor.textPrimary)
                .lineLimit(1)
                .minimumScaleFactor(0.7)

            // Change percent
            Text(ticker.changePercent.asPercentage)
                .font(MPFont.monoMedium())
                .gainLossColored(value: ticker.changePercent)

            // Optional note
            if let note = ticker.note, !note.isEmpty {
                Text(note)
                    .font(MPFont.caption())
                    .foregroundStyle(MPColor.textTertiary)
                    .lineLimit(2)
                    .multilineTextAlignment(.center)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(MPSpacing.card)
        .background(MPColor.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: MPRadius.card))
        .overlay(
            RoundedRectangle(cornerRadius: MPRadius.card)
                .strokeBorder(
                    MPColor.forValue(ticker.changePercent).opacity(0.3),
                    lineWidth: 1
                )
        )
    }
}

#Preview {
    ZStack {
        MPColor.background.ignoresSafeArea()
        ScrollView {
            KeyTickersSectionView(
                tickers: [
                    KeyTicker(id: "1", ticker: "AAPL", price: 187.44, changePercent: 2.35, note: "New iPhone launch"),
                    KeyTicker(id: "2", ticker: "TSLA", price: 241.10, changePercent: -4.12, note: "Delivery miss"),
                    KeyTicker(id: "3", ticker: "NVDA", price: 875.30, changePercent: 5.42, note: nil),
                    KeyTicker(id: "4", ticker: "MSFT", price: 415.00, changePercent: 0.78, note: "Azure growth"),
                ]
            )
        }
    }
}
