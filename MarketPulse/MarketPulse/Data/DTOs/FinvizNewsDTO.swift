import Foundation

struct FinvizNewsDTO: Sendable {
    let date: String
    let time: String?
    let ticker: String?
    let title: String
    let link: String
    let source: String

    /// Failable initializer that accepts a CSV row dictionary with flexible column name lookup.
    /// Recognizes common FINVIZ Elite column header variations.
    init?(row: [String: String]) {
        guard let date = row["Date"] ?? row["date"],
              let title = row["Title"] ?? row["Headline"] ?? row["title"] ?? row["headline"],
              let link = row["Link"] ?? row["URL"] ?? row["link"] ?? row["url"],
              let source = row["Source"] ?? row["source"]
        else {
            return nil
        }

        let trimmedDate = date.trimmingCharacters(in: .whitespaces)
        let trimmedTitle = title.trimmingCharacters(in: .whitespaces)
        let trimmedLink = link.trimmingCharacters(in: .whitespaces)
        let trimmedSource = source.trimmingCharacters(in: .whitespaces)

        guard !trimmedDate.isEmpty, !trimmedTitle.isEmpty, !trimmedLink.isEmpty, !trimmedSource.isEmpty else {
            return nil
        }

        self.date = trimmedDate
        self.time = (row["Time"] ?? row["time"])?.trimmingCharacters(in: .whitespaces)
        self.ticker = (row["Ticker"] ?? row["ticker"])?.trimmingCharacters(in: .whitespaces)
        self.title = trimmedTitle
        self.link = trimmedLink
        self.source = trimmedSource
    }
}
