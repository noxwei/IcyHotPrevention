import Foundation

struct FinvizPortfolioDTO: Sendable {
    let ticker: String
    let company: String
    let sector: String?
    let industry: String?
    let marketCap: String?
    let pe: String?
    let price: String
    let change: String
    let volume: String

    /// Failable initializer that accepts a CSV row dictionary with flexible column name lookup.
    /// Recognizes common FINVIZ Elite portfolio export column headers.
    init?(row: [String: String]) {
        guard let ticker = row["Ticker"] ?? row["ticker"],
              let company = row["Company"] ?? row["company"],
              let price = row["Price"] ?? row["price"],
              let change = row["Change"] ?? row["change"],
              let volume = row["Volume"] ?? row["volume"]
        else {
            return nil
        }

        let trimmedTicker = ticker.trimmingCharacters(in: .whitespaces)
        let trimmedCompany = company.trimmingCharacters(in: .whitespaces)
        let trimmedPrice = price.trimmingCharacters(in: .whitespaces)
        let trimmedChange = change.trimmingCharacters(in: .whitespaces)
        let trimmedVolume = volume.trimmingCharacters(in: .whitespaces)

        guard !trimmedTicker.isEmpty, !trimmedCompany.isEmpty,
              !trimmedPrice.isEmpty, !trimmedVolume.isEmpty else {
            return nil
        }

        self.ticker = trimmedTicker
        self.company = trimmedCompany
        self.sector = (row["Sector"] ?? row["sector"])?.trimmingCharacters(in: .whitespaces)
        self.industry = (row["Industry"] ?? row["industry"])?.trimmingCharacters(in: .whitespaces)
        self.marketCap = (row["Market Cap"] ?? row["MarketCap"] ?? row["market cap"])?.trimmingCharacters(in: .whitespaces)
        self.pe = (row["P/E"] ?? row["PE"] ?? row["p/e"])?.trimmingCharacters(in: .whitespaces)
        self.price = trimmedPrice
        self.change = trimmedChange
        self.volume = trimmedVolume
    }
}
