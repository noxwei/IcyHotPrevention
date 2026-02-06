import SwiftUI

/// Reusable section header with an emoji, uppercased title, and optional trailing action.
struct SectionHeaderView: View {
    let emoji: String
    let title: String
    var seeAllAction: (() -> Void)?

    var body: some View {
        HStack(alignment: .center) {
            Text("\(emoji) \(title.uppercased())")
                .font(MPFont.sectionTitle())
                .foregroundStyle(MPColor.textPrimary)
                .tracking(1.5)

            Spacer()

            if let seeAllAction {
                Button(action: seeAllAction) {
                    Text("See All")
                        .font(MPFont.caption())
                        .foregroundStyle(MPColor.accent)
                }
            }
        }
        .padding(.horizontal, MPSpacing.card)
        .padding(.bottom, MPSpacing.tight)
    }
}

#Preview {
    ZStack {
        MPColor.background.ignoresSafeArea()
        VStack(spacing: MPSpacing.card) {
            SectionHeaderView(emoji: "\u{1F4C8}", title: "Market Moves")
            SectionHeaderView(emoji: "\u{1F4CA}", title: "Sector Rotation") {
                // no-op
            }
        }
    }
}
