import Foundation

/// Maps a single element from the JSON array returned by Finnhub `GET /news`.
struct FinnhubNewsDTO: Codable, Sendable {
    let category: String
    let datetime: Int
    let headline: String
    let id: Int
    let image: String
    let related: String
    let source: String
    let summary: String
    let url: String
}
