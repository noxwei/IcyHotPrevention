import SwiftUI

/// Red-tinted banner displaying an error message with a "Retry" button.
struct ErrorBannerView: View {
    let message: String
    let onRetry: () -> Void

    var body: some View {
        VStack(spacing: MPSpacing.card) {
            // Error icon
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 36))
                .foregroundStyle(MPColor.loss.opacity(0.8))

            // Error message
            Text(message)
                .font(MPFont.body())
                .foregroundStyle(MPColor.textSecondary)
                .multilineTextAlignment(.center)
                .lineLimit(4)
                .padding(.horizontal, MPSpacing.section)

            // Retry button
            Button(action: onRetry) {
                HStack(spacing: MPSpacing.item) {
                    Image(systemName: "arrow.clockwise")
                    Text("Retry")
                }
                .font(MPFont.body())
                .foregroundStyle(MPColor.textPrimary)
                .padding(.horizontal, MPSpacing.section)
                .padding(.vertical, MPSpacing.item)
                .background(MPColor.loss.opacity(0.2))
                .clipShape(RoundedRectangle(cornerRadius: MPRadius.badge))
                .overlay(
                    RoundedRectangle(cornerRadius: MPRadius.badge)
                        .strokeBorder(MPColor.loss.opacity(0.4), lineWidth: 1)
                )
            }
        }
        .padding(MPSpacing.section)
        .frame(maxWidth: .infinity)
        .background(
            RoundedRectangle(cornerRadius: MPRadius.card)
                .fill(MPColor.loss.opacity(0.08))
        )
        .overlay(
            RoundedRectangle(cornerRadius: MPRadius.card)
                .strokeBorder(MPColor.loss.opacity(0.2), lineWidth: 1)
        )
        .padding(.horizontal, MPSpacing.card)
    }
}

#Preview {
    ZStack {
        MPColor.background.ignoresSafeArea()
        ErrorBannerView(
            message: "Network error (HTTP 429): Rate limit exceeded. Please wait before making another request."
        ) {
            // retry action
        }
    }
}
