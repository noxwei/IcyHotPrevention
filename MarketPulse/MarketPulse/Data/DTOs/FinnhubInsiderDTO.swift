import Foundation

/// Maps the top-level JSON response from Finnhub `GET /stock/insider-transactions`.
struct FinnhubInsiderResponse: Codable, Sendable {
    let data: [FinnhubInsiderDTO]
    let symbol: String
}

/// Maps a single insider transaction entry within the response.
struct FinnhubInsiderDTO: Codable, Sendable {
    let name: String
    let share: Int
    let change: Int
    let filingDate: String
    let transactionDate: String
    let transactionCode: String
    let transactionPrice: Double
}
