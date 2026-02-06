import Foundation

/// Maps the JSON response from Finnhub `GET /stock/profile2`.
struct FinnhubCompanyDTO: Codable, Sendable {
    let country: String?
    let currency: String?
    let exchange: String?
    let finnhubIndustry: String?
    let ipo: String?
    let logo: String?
    let marketCapitalization: Double?
    let name: String?
    let phone: String?
    let shareOutstanding: Double?
    let ticker: String?
    let weburl: String?
}
