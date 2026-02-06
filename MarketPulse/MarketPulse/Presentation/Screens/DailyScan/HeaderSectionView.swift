import SwiftUI

/// "MARKET PULSE" centered header with date and time below in monospace.
struct HeaderSectionView: View {
    let date: Date

    var body: some View {
        VStack(spacing: MPSpacing.item) {
            // App title
            Text("MARKET PULSE")
                .font(MPFont.headerLarge())
                .foregroundStyle(MPColor.textPrimary)
                .tracking(4)
                .multilineTextAlignment(.center)

            // Date line
            Text(date.estFormatted)
                .font(MPFont.monoMedium())
                .foregroundStyle(MPColor.textSecondary)

            // Time line with market status
            HStack(spacing: MPSpacing.item) {
                Text(date.estTime)
                    .font(MPFont.monoSmall())
                    .foregroundStyle(MPColor.textTertiary)

                Text("\u{2022}")
                    .font(MPFont.monoSmall())
                    .foregroundStyle(MPColor.textTertiary)

                Text(date.marketStatusLabel)
                    .font(MPFont.monoSmall())
                    .foregroundStyle(marketStatusColor)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, MPSpacing.card)
    }

    private var marketStatusColor: Color {
        switch date.marketStatusLabel {
        case "Market Open": return MPColor.gain
        case "Pre-Market": return MPColor.accent
        case "After Hours": return MPColor.hotSector
        default: return MPColor.textTertiary
        }
    }
}

#Preview {
    ZStack {
        MPColor.background.ignoresSafeArea()
        HeaderSectionView(date: Date())
    }
}
