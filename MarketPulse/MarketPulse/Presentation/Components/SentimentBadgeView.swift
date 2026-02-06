import SwiftUI

/// Large centered sentiment badge: emoji circle + "Bullish"/"Bearish"/"Neutral" label.
struct SentimentBadgeView: View {
    let sentiment: MarketSentiment

    private var badgeColor: Color {
        switch sentiment {
        case .bullish: return MPColor.gain
        case .bearish: return MPColor.loss
        case .neutral: return MPColor.neutral
        }
    }

    var body: some View {
        VStack(spacing: MPSpacing.item) {
            // Emoji circle
            Text(sentiment.emoji)
                .font(.system(size: 48))
                .frame(width: 80, height: 80)
                .background(
                    Circle()
                        .fill(badgeColor.opacity(0.15))
                )
                .overlay(
                    Circle()
                        .strokeBorder(badgeColor.opacity(0.4), lineWidth: 2)
                )

            // Label
            Text(sentiment.label.uppercased())
                .font(MPFont.sectionTitle())
                .foregroundStyle(badgeColor)
                .tracking(3)
        }
    }
}

#Preview {
    ZStack {
        MPColor.background.ignoresSafeArea()
        HStack(spacing: 40) {
            SentimentBadgeView(sentiment: .bullish)
            SentimentBadgeView(sentiment: .bearish)
            SentimentBadgeView(sentiment: .neutral)
        }
    }
}
