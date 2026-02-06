import SwiftUI

/// "VOLUME SIGNALS" section listing unusual volume activity.
struct VolumeSectionView: View {
    let signals: [VolumeSignal]

    var body: some View {
        VStack(alignment: .leading, spacing: MPSpacing.card) {
            SectionHeaderView(emoji: "\u{1F4E2}", title: "Volume Signals")

            VStack(alignment: .leading, spacing: MPSpacing.item) {
                ForEach(signals) { signal in
                    VolumeSignalRow(signal: signal)
                }
            }
            .cardStyle()
            .padding(.horizontal, MPSpacing.card)
        }
    }
}

// MARK: - Volume Signal Row

private struct VolumeSignalRow: View {
    let signal: VolumeSignal

    var body: some View {
        HStack(alignment: .top, spacing: MPSpacing.item) {
            // Volume ratio indicator
            VolumeRatioBadge(ratio: signal.volumeRatio)

            VStack(alignment: .leading, spacing: MPSpacing.tight) {
                HStack(spacing: MPSpacing.tight) {
                    Text("$\(signal.ticker)")
                        .font(MPFont.monoMedium())
                        .foregroundStyle(MPColor.textPrimary)

                    Text("trading")
                        .font(MPFont.body())
                        .foregroundStyle(MPColor.textTertiary)

                    Text(signal.volumeFormatted)
                        .font(MPFont.monoMedium())
                        .foregroundStyle(MPColor.accent)

                    Text("shares")
                        .font(MPFont.body())
                        .foregroundStyle(MPColor.textTertiary)
                }

                HStack(spacing: MPSpacing.tight) {
                    Text("(\(signal.changePercent.asPercentage))")
                        .font(MPFont.monoSmall())
                        .gainLossColored(value: signal.changePercent)

                    if !signal.reason.isEmpty {
                        Text("on \(signal.reason)")
                            .font(MPFont.caption())
                            .foregroundStyle(MPColor.textTertiary)
                            .lineLimit(2)
                    }
                }
            }

            Spacer(minLength: 0)
        }
        .padding(.vertical, MPSpacing.tight)
    }
}

// MARK: - Volume Ratio Badge

private struct VolumeRatioBadge: View {
    let ratio: Double

    private var intensity: Color {
        switch ratio {
        case 3...: return MPColor.loss
        case 2..<3: return MPColor.hotSector
        default: return MPColor.accent
        }
    }

    var body: some View {
        Text(String(format: "%.1fx", ratio))
            .font(MPFont.caption())
            .foregroundStyle(intensity)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(intensity.opacity(0.15))
            .clipShape(RoundedRectangle(cornerRadius: MPRadius.chip))
    }
}

#Preview {
    ZStack {
        MPColor.background.ignoresSafeArea()
        ScrollView {
            VolumeSectionView(
                signals: [
                    VolumeSignal(id: "1", ticker: "NVDA", volume: 85_000_000, averageVolume: 35_000_000, changePercent: 5.42, reason: "earnings beat"),
                    VolumeSignal(id: "2", ticker: "BA", volume: 32_000_000, averageVolume: 12_000_000, changePercent: -3.10, reason: "FAA investigation"),
                ]
            )
        }
    }
}
