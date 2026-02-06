import Foundation

/// Splits market movers into top gainers and top losers, ranked by the
/// magnitude of their daily percentage change.
struct IdentifyMoversUseCase: Sendable {

    func identify(
        from movers: [MarketMover],
        topN: Int = 5
    ) -> (gainers: [MarketMover], losers: [MarketMover]) {

        let sorted = movers.sorted {
            abs($0.changePercent) > abs($1.changePercent)
        }

        let gainers = sorted
            .filter { $0.changePercent > 0 }
            .prefix(topN)

        let losers = sorted
            .filter { $0.changePercent < 0 }
            .prefix(topN)

        return (gainers: Array(gainers), losers: Array(losers))
    }
}
