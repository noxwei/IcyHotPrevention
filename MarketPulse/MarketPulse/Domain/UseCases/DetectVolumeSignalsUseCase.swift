import Foundation

/// Detects unusual volume activity from market movers by comparing current
/// volume against the average volume.
struct DetectVolumeSignalsUseCase: Sendable {

    func detect(
        from movers: [MarketMover],
        threshold: Double = 2.0
    ) -> [VolumeSignal] {

        movers
            .filter { $0.volumeRatio > threshold }
            .sorted { $0.volumeRatio > $1.volumeRatio }
            .prefix(5)
            .map { mover in
                VolumeSignal(
                    id: mover.ticker,
                    ticker: mover.ticker,
                    volume: mover.volume,
                    averageVolume: mover.averageVolume,
                    changePercent: mover.changePercent,
                    reason: classifyReason(changePercent: mover.changePercent)
                )
            }
    }

    // MARK: - Private

    private func classifyReason(changePercent: Double) -> String {
        let magnitude = abs(changePercent)
        if magnitude > 10 {
            return "earnings"
        } else if magnitude > 5 {
            return "news"
        } else {
            return "unusual"
        }
    }
}
