import Foundation

/// Builds a consolidated watch list from top movers, news mentions, and
/// volume signals, deduplicating by ticker.
struct BuildWatchListUseCase: Sendable {

    func build(
        movers: [MarketMover],
        news: [NewsItem],
        volumeSignals: [VolumeSignal]
    ) -> [WatchItem] {

        var seen = Set<String>()
        var items: [WatchItem] = []

        // 1. Top 3 movers by absolute changePercent
        let topMovers = movers
            .sorted { abs($0.changePercent) > abs($1.changePercent) }
            .prefix(3)

        for mover in topMovers {
            let ticker = mover.ticker
            guard !seen.contains(ticker) else { continue }
            seen.insert(ticker)

            let direction = mover.isGainer ? "gaining" : "losing"
            let reason = "Top mover: \(direction) \(formatted(mover.changePercent))%"
            items.append(WatchItem(id: ticker, ticker: ticker, reason: reason))
        }

        // 2. Tickers mentioned in top 5 news
        let newsWithTickers = news
            .sorted { $0.timestamp > $1.timestamp }
            .prefix(5)
            .compactMap { item -> (String, String)? in
                guard let ticker = item.ticker else { return nil }
                return (ticker, "In the news: \(item.headline)")
            }

        for (ticker, reason) in newsWithTickers {
            guard !seen.contains(ticker) else { continue }
            seen.insert(ticker)
            items.append(WatchItem(id: ticker, ticker: ticker, reason: reason))
        }

        // 3. Volume signals
        for signal in volumeSignals {
            let ticker = signal.ticker
            guard !seen.contains(ticker) else { continue }
            seen.insert(ticker)

            let ratio = String(format: "%.1f", signal.volumeRatio)
            let reason = "Volume signal: \(ratio)x avg (\(signal.reason))"
            items.append(WatchItem(id: ticker, ticker: ticker, reason: reason))
        }

        return Array(items.prefix(7))
    }

    // MARK: - Private

    private func formatted(_ value: Double) -> String {
        String(format: "%+.1f", value)
    }
}
