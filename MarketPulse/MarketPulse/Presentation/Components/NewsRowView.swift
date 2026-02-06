import SwiftUI

/// A single news row: bullet + headline + (source). Tappable if a URL is available.
struct NewsRowView: View {
    let headline: String
    let source: String
    let url: URL?
    let ticker: String?

    var body: some View {
        Group {
            if let url {
                Link(destination: url) {
                    rowContent
                }
            } else {
                rowContent
            }
        }
    }

    private var rowContent: some View {
        HStack(alignment: .top, spacing: MPSpacing.item) {
            Text("\u{2022}")
                .font(MPFont.body())
                .foregroundStyle(MPColor.textTertiary)
                .padding(.top, 1)

            VStack(alignment: .leading, spacing: MPSpacing.tight) {
                HStack(spacing: MPSpacing.tight) {
                    if let ticker {
                        Text("$\(ticker)")
                            .font(MPFont.monoSmall())
                            .foregroundStyle(MPColor.accent)
                    }

                    Text(headline)
                        .font(MPFont.body())
                        .foregroundStyle(MPColor.textPrimary)
                        .lineLimit(3)
                        .multilineTextAlignment(.leading)
                }

                Text("(\(source))")
                    .font(MPFont.caption())
                    .foregroundStyle(MPColor.textTertiary)
            }

            Spacer(minLength: 0)
        }
    }
}

#Preview {
    ZStack {
        MPColor.background.ignoresSafeArea()
        VStack(spacing: MPSpacing.item) {
            NewsRowView(
                headline: "Apple reports record Q4 earnings beating estimates",
                source: "Reuters",
                url: URL(string: "https://reuters.com"),
                ticker: "AAPL"
            )
            NewsRowView(
                headline: "Fed signals potential rate cut in upcoming meeting",
                source: "Bloomberg",
                url: nil,
                ticker: nil
            )
        }
        .padding()
    }
}
