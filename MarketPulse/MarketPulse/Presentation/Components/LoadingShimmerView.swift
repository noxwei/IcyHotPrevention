import SwiftUI

/// Animated shimmer placeholder mimicking the daily scan layout.
/// Gray rectangles pulse with a gradient to indicate loading.
struct LoadingShimmerView: View {
    @State private var isAnimating = false

    var body: some View {
        VStack(spacing: MPSpacing.section) {
            // Header placeholder
            shimmerBlock(width: 180, height: 28)
            shimmerBlock(width: 220, height: 14)

            // Sentiment placeholder
            shimmerCircle(size: 80)

            // Index cards placeholder
            HStack(spacing: MPSpacing.item) {
                shimmerCard()
                shimmerCard()
                shimmerCard()
            }
            .padding(.horizontal, MPSpacing.card)

            // Section placeholders
            ForEach(0..<4, id: \.self) { _ in
                VStack(alignment: .leading, spacing: MPSpacing.item) {
                    shimmerBlock(width: 160, height: 16)
                        .padding(.horizontal, MPSpacing.card)

                    ForEach(0..<3, id: \.self) { _ in
                        shimmerBlock(height: 12)
                            .padding(.horizontal, MPSpacing.card)
                    }
                }
            }
        }
        .padding(.top, MPSpacing.section)
        .onAppear {
            withAnimation(
                .easeInOut(duration: 1.2)
                .repeatForever(autoreverses: true)
            ) {
                isAnimating = true
            }
        }
    }

    private func shimmerBlock(width: CGFloat? = nil, height: CGFloat = 14) -> some View {
        RoundedRectangle(cornerRadius: 4)
            .fill(MPColor.surface)
            .frame(width: width, height: height)
            .opacity(isAnimating ? 0.4 : 0.8)
    }

    private func shimmerCircle(size: CGFloat) -> some View {
        Circle()
            .fill(MPColor.surface)
            .frame(width: size, height: size)
            .opacity(isAnimating ? 0.4 : 0.8)
    }

    private func shimmerCard() -> some View {
        RoundedRectangle(cornerRadius: MPRadius.card)
            .fill(MPColor.cardBackground)
            .frame(height: 80)
            .opacity(isAnimating ? 0.5 : 0.9)
    }
}

#Preview {
    ZStack {
        MPColor.background.ignoresSafeArea()
        ScrollView {
            LoadingShimmerView()
        }
    }
}
