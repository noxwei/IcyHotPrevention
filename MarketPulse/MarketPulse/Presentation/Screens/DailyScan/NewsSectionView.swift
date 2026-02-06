import SwiftUI

/// Two subsections: "CORPORATE" and "MACRO" news, each showing up to 5 headlines.
struct NewsSectionView: View {
    let corporateNews: [NewsItem]
    let macroNews: [NewsItem]

    /// Maximum number of news items to show per category.
    private let maxItems = 5

    var body: some View {
        VStack(alignment: .leading, spacing: MPSpacing.section) {
            // Corporate News
            if !corporateNews.isEmpty {
                VStack(alignment: .leading, spacing: MPSpacing.item) {
                    SectionHeaderView(emoji: "\u{1F3E2}", title: "Corporate")

                    VStack(alignment: .leading, spacing: MPSpacing.item) {
                        ForEach(corporateNews.prefix(maxItems)) { item in
                            NewsRowView(
                                headline: item.headline,
                                source: item.source,
                                url: item.url,
                                ticker: item.ticker
                            )
                        }
                    }
                    .padding(.horizontal, MPSpacing.card)
                }
            }

            // Macro News
            if !macroNews.isEmpty {
                VStack(alignment: .leading, spacing: MPSpacing.item) {
                    SectionHeaderView(emoji: "\u{1F30E}", title: "Macro")

                    VStack(alignment: .leading, spacing: MPSpacing.item) {
                        ForEach(macroNews.prefix(maxItems)) { item in
                            NewsRowView(
                                headline: item.headline,
                                source: item.source,
                                url: item.url,
                                ticker: item.ticker
                            )
                        }
                    }
                    .padding(.horizontal, MPSpacing.card)
                }
            }
        }
    }
}

#Preview {
    ZStack {
        MPColor.background.ignoresSafeArea()
        ScrollView {
            NewsSectionView(
                corporateNews: [
                    NewsItem(id: UUID(), timestamp: Date(), headline: "Apple reports record Q4 earnings", source: "Reuters", ticker: "AAPL", url: nil, category: .corporate),
                    NewsItem(id: UUID(), timestamp: Date(), headline: "Tesla recalls 2M vehicles over autopilot", source: "Bloomberg", ticker: "TSLA", url: nil, category: .corporate),
                ],
                macroNews: [
                    NewsItem(id: UUID(), timestamp: Date(), headline: "Fed signals potential rate cut in March", source: "CNBC", ticker: nil, url: nil, category: .macro),
                ]
            )
        }
    }
}
