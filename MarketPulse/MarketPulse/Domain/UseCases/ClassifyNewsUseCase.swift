import Foundation

/// Classifies news items into macro-economic and corporate buckets using
/// keyword matching on the headline.
struct ClassifyNewsUseCase: Sendable {

    // MARK: - Macro keywords (all lowercase for case-insensitive matching)

    private static let macroKeywords: [String] = [
        "fed", "inflation", "gdp", "jobs", "unemployment",
        "cpi", "ppi", "fomc", "rate", "treasury",
        "yield", "economic", "trade", "tariff", "sanctions",
        "oil", "gold", "commodity", "housing", "consumer",
        "retail sales", "manufacturing"
    ]

    // MARK: - Public API

    func classify(
        _ news: [NewsItem]
    ) -> (corporate: [NewsItem], macro: [NewsItem]) {

        var corporate: [NewsItem] = []
        var macro: [NewsItem] = []

        for item in news {
            let lowered = item.headline.lowercased()
            let isMacro = Self.macroKeywords.contains { lowered.contains($0) }

            if isMacro {
                macro.append(item.withCategory(.macro))
            } else {
                corporate.append(item.withCategory(.corporate))
            }
        }

        // Most recent first, capped at 5 each
        let sortedCorporate = corporate
            .sorted { $0.timestamp > $1.timestamp }
            .prefix(5)

        let sortedMacro = macro
            .sorted { $0.timestamp > $1.timestamp }
            .prefix(5)

        return (corporate: Array(sortedCorporate), macro: Array(sortedMacro))
    }
}
