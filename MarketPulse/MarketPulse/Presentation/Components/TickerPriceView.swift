import SwiftUI

/// Compact inline view: $TICKER price (+X.XX%) with monospace and gain/loss coloring.
struct TickerPriceView: View {
    let ticker: String
    let price: Double
    let changePercent: Double

    var body: some View {
        HStack(spacing: MPSpacing.tight) {
            Text("$\(ticker)")
                .font(MPFont.monoMedium())
                .foregroundStyle(MPColor.textPrimary)

            Text(price.asCurrency)
                .font(MPFont.monoMedium())
                .foregroundStyle(MPColor.textSecondary)

            Text("(\(changePercent.asPercentage))")
                .font(MPFont.monoSmall())
                .gainLossColored(value: changePercent)
        }
    }
}

#Preview {
    ZStack {
        MPColor.background.ignoresSafeArea()
        VStack(spacing: MPSpacing.item) {
            TickerPriceView(ticker: "AAPL", price: 187.44, changePercent: 2.35)
            TickerPriceView(ticker: "TSLA", price: 241.10, changePercent: -4.12)
            TickerPriceView(ticker: "MSFT", price: 415.00, changePercent: 0.0)
        }
    }
}
