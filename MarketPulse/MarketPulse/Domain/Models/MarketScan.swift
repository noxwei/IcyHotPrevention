import Foundation

struct MarketScan: Identifiable, Codable, Sendable {
    let id: UUID
    let generatedAt: Date
    let sentiment: MarketSentiment
    let indexSnapshots: [IndexSnapshot]
    let topGainers: [MarketMover]
    let topLosers: [MarketMover]
    let corporateNews: [NewsItem]
    let macroNews: [NewsItem]
    let hotSectors: [SectorRotation]
    let coldSectors: [SectorRotation]
    let rotationNotes: String
    let volumeSignals: [VolumeSignal]
    let keyTickers: [KeyTicker]
    let quickTake: QuickTake?
    let watchList: [WatchItem]

    func withQuickTake(_ qt: QuickTake) -> MarketScan {
        MarketScan(
            id: id,
            generatedAt: generatedAt,
            sentiment: sentiment,
            indexSnapshots: indexSnapshots,
            topGainers: topGainers,
            topLosers: topLosers,
            corporateNews: corporateNews,
            macroNews: macroNews,
            hotSectors: hotSectors,
            coldSectors: coldSectors,
            rotationNotes: rotationNotes,
            volumeSignals: volumeSignals,
            keyTickers: keyTickers,
            quickTake: qt,
            watchList: watchList
        )
    }
}
