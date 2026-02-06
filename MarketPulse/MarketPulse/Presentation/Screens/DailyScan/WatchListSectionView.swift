import SwiftUI

/// "WATCH LIST" section with horizontal scroll of ticker chips.
struct WatchListSectionView: View {
    let items: [WatchItem]

    var body: some View {
        VStack(alignment: .leading, spacing: MPSpacing.card) {
            SectionHeaderView(emoji: "\u{1F440}", title: "Watch List")

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: MPSpacing.item) {
                    ForEach(items) { item in
                        WatchChipView(item: item)
                    }
                }
                .padding(.horizontal, MPSpacing.card)
            }
        }
    }
}

// MARK: - Watch Chip

private struct WatchChipView: View {
    let item: WatchItem

    var body: some View {
        VStack(alignment: .leading, spacing: MPSpacing.tight) {
            Text("$\(item.ticker)")
                .font(MPFont.monoMedium())
                .foregroundStyle(MPColor.accent)

            Text(item.reason)
                .font(MPFont.caption())
                .foregroundStyle(MPColor.textTertiary)
                .lineLimit(2)
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(width: 120)
        .padding(MPSpacing.item)
        .background(MPColor.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: MPRadius.badge))
        .overlay(
            RoundedRectangle(cornerRadius: MPRadius.badge)
                .strokeBorder(MPColor.accent.opacity(0.2), lineWidth: 1)
        )
    }
}

#Preview {
    ZStack {
        MPColor.background.ignoresSafeArea()
        WatchListSectionView(
            items: [
                WatchItem(id: "1", ticker: "AAPL", reason: "Earnings next week"),
                WatchItem(id: "2", ticker: "TSLA", reason: "Key support at $230"),
                WatchItem(id: "3", ticker: "AMD", reason: "New chip announcement"),
                WatchItem(id: "4", ticker: "GOOG", reason: "Antitrust ruling pending"),
            ]
        )
    }
}
