import Foundation

struct NewsItem: Identifiable, Codable, Sendable {
    let id: UUID
    let timestamp: Date
    let headline: String
    let source: String
    let ticker: String?
    let url: URL?
    let category: NewsCategory

    enum NewsCategory: String, Codable, Sendable {
        case corporate
        case macro
        case unknown
    }

    func withCategory(_ cat: NewsCategory) -> NewsItem {
        NewsItem(
            id: id,
            timestamp: timestamp,
            headline: headline,
            source: source,
            ticker: ticker,
            url: url,
            category: cat
        )
    }
}
