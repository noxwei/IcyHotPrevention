import Foundation

/// Determines the overall market sentiment from a set of index snapshots.
///
/// Rules:
/// - 2+ positive indexes AND average changePercent > 0.3  ->  bullish
/// - 1 or fewer positive AND average changePercent < -0.3 ->  bearish
/// - Otherwise                                             ->  neutral
struct CalculateSentimentUseCase: Sendable {

    func calculate(from snapshots: [IndexSnapshot]) -> MarketSentiment {
        guard !snapshots.isEmpty else { return .neutral }

        let positiveCount = snapshots.filter { $0.changePercent > 0 }.count

        let averageChange = snapshots.reduce(0.0) { $0 + $1.changePercent }
            / Double(snapshots.count)

        if positiveCount >= 2, averageChange > 0.3 {
            return .bullish
        } else if positiveCount <= 1, averageChange < -0.3 {
            return .bearish
        } else {
            return .neutral
        }
    }
}
