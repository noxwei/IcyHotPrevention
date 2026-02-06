import SwiftUI

/// Main Daily Scan view composing all 12 sections in a scrollable layout.
/// Pull-to-refresh. Dark background. Shows shimmer while loading, error banner on failure.
struct DailyScanView: View {
    @Bindable var viewModel: DailyScanViewModel

    var body: some View {
        ZStack {
            MPColor.background
                .ignoresSafeArea()

            Group {
                if viewModel.isLoading && viewModel.scan == nil {
                    // Initial loading state
                    ScrollView {
                        LoadingShimmerView()
                    }
                    .scrollIndicators(.hidden)
                } else if let scan = viewModel.scan {
                    // Scan loaded
                    scanContent(scan)
                } else if let error = viewModel.error {
                    // Error with no data
                    ScrollView {
                        VStack {
                            Spacer(minLength: 80)
                            ErrorBannerView(message: error) {
                                Task { await viewModel.refresh() }
                            }
                            Spacer()
                        }
                    }
                } else {
                    // Empty initial state
                    ScrollView {
                        VStack {
                            Spacer(minLength: 120)
                            Text("Pull to scan the market")
                                .font(MPFont.body())
                                .foregroundStyle(MPColor.textTertiary)
                            Spacer()
                        }
                    }
                }
            }
        }
        .task {
            if viewModel.scan == nil {
                await viewModel.loadScan()
            }
        }
    }

    // MARK: - Scan Content

    @ViewBuilder
    private func scanContent(_ scan: MarketScan) -> some View {
        ScrollView {
            LazyVStack(spacing: MPSpacing.section) {

                // 1. Header
                HeaderSectionView(date: scan.generatedAt)

                // Inline error banner (if refresh failed but we have stale data)
                if let error = viewModel.error {
                    ErrorBannerView(message: error) {
                        Task { await viewModel.refresh() }
                    }
                }

                // 2. Sentiment + Index Cards
                SentimentSectionView(
                    sentiment: scan.sentiment,
                    indexSnapshots: scan.indexSnapshots
                )

                SectionDivider()

                // 3. Market Moves
                MoversSectionView(
                    gainers: scan.topGainers,
                    losers: scan.topLosers
                )

                SectionDivider()

                // 4. News (Corporate + Macro)
                NewsSectionView(
                    corporateNews: scan.corporateNews,
                    macroNews: scan.macroNews
                )

                SectionDivider()

                // 5. Sector Rotation
                SectorsSectionView(
                    hotSectors: scan.hotSectors,
                    coldSectors: scan.coldSectors,
                    rotationNotes: scan.rotationNotes
                )

                SectionDivider()

                // 6. Volume Signals
                if !scan.volumeSignals.isEmpty {
                    VolumeSectionView(signals: scan.volumeSignals)
                    SectionDivider()
                }

                // 7. Key Tickers
                if !scan.keyTickers.isEmpty {
                    KeyTickersSectionView(tickers: scan.keyTickers)
                    SectionDivider()
                }

                // 8. Quick Take
                if let quickTake = scan.quickTake {
                    QuickTakeSectionView(quickTake: quickTake)
                    SectionDivider()
                }

                // 9. Watch List
                if !scan.watchList.isEmpty {
                    WatchListSectionView(items: scan.watchList)
                }

                // Footer
                footerView
            }
            .padding(.bottom, MPSpacing.section)
        }
        .scrollIndicators(.hidden)
        .refreshable {
            await viewModel.refresh()
        }
    }

    // MARK: - Footer

    private var footerView: some View {
        VStack(spacing: MPSpacing.tight) {
            Text("End scan.")
                .font(MPFont.monoSmall())
                .foregroundStyle(MPColor.textTertiary)
                .italic()

            if let lastRefreshed = viewModel.lastRefreshed {
                Text("Last refreshed: \(lastRefreshed.estTime)")
                    .font(MPFont.caption())
                    .foregroundStyle(MPColor.textTertiary)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.top, MPSpacing.card)
        .padding(.bottom, MPSpacing.section)
    }
}

#Preview {
    let vm = DailyScanViewModel {
        // Simulated scan for preview
        try await Task.sleep(for: .seconds(1))
        return MarketScan(
            id: UUID(),
            generatedAt: Date(),
            sentiment: .bullish,
            indexSnapshots: [
                IndexSnapshot(id: "SPY", name: "SPY", price: 502.34, change: 4.56, changePercent: 0.92, high: 505.10, low: 498.20, previousClose: 497.78),
                IndexSnapshot(id: "QQQ", name: "QQQ", price: 432.10, change: -2.30, changePercent: -0.53, high: 435.00, low: 430.50, previousClose: 434.40),
                IndexSnapshot(id: "DIA", name: "DIA", price: 389.55, change: 1.23, changePercent: 0.32, high: 391.00, low: 387.00, previousClose: 388.32),
            ],
            topGainers: [
                MarketMover(id: "g1", ticker: "NVDA", companyName: "NVIDIA", price: 875.30, changePercent: 5.42, volume: 45_000_000, averageVolume: 30_000_000, sector: "Technology"),
            ],
            topLosers: [
                MarketMover(id: "l1", ticker: "BA", companyName: "Boeing", price: 178.45, changePercent: -4.56, volume: 18_000_000, averageVolume: 10_000_000, sector: "Industrials"),
            ],
            corporateNews: [
                NewsItem(id: UUID(), timestamp: Date(), headline: "Apple reports record Q4 earnings", source: "Reuters", ticker: "AAPL", url: nil, category: .corporate),
            ],
            macroNews: [
                NewsItem(id: UUID(), timestamp: Date(), headline: "Fed signals potential rate cut", source: "CNBC", ticker: nil, url: nil, category: .macro),
            ],
            hotSectors: [
                SectorRotation(id: "tech", name: "Technology", changePercent: 3.45, leadingTickers: ["AAPL", "MSFT"]),
            ],
            coldSectors: [
                SectorRotation(id: "energy", name: "Energy", changePercent: -2.80, leadingTickers: ["XOM"]),
            ],
            rotationNotes: "Money rotating into tech on strong earnings. Defensive sectors lagging.",
            volumeSignals: [
                VolumeSignal(id: "v1", ticker: "NVDA", volume: 85_000_000, averageVolume: 35_000_000, changePercent: 5.42, reason: "earnings beat"),
            ],
            keyTickers: [
                KeyTicker(id: "k1", ticker: "AAPL", price: 187.44, changePercent: 2.35, note: "Earnings"),
                KeyTicker(id: "k2", ticker: "TSLA", price: 241.10, changePercent: -4.12, note: nil),
            ],
            quickTake: QuickTake(text: "Markets showed mixed signals today with tech leading gains.", provider: "Claude API", generatedAt: Date()),
            watchList: [
                WatchItem(id: "w1", ticker: "AAPL", reason: "Earnings next week"),
                WatchItem(id: "w2", ticker: "AMD", reason: "New chip launch"),
            ]
        )
    }

    DailyScanView(viewModel: vm)
}
