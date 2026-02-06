import Foundation

extension Date {

    // MARK: - Private Helpers

    /// The America/New_York time zone used throughout the app for market-hours logic.
    private static let easternTimeZone: TimeZone = {
        guard let tz = TimeZone(identifier: "America/New_York") else {
            // Fallback should never be needed, but keeps us safe.
            return TimeZone(secondsFromGMT: -5 * 3600)!
        }
        return tz
    }()

    /// Calendar configured for Eastern Time calculations.
    private static var easternCalendar: Calendar {
        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = easternTimeZone
        return cal
    }

    // MARK: - Formatted Strings

    /// Full date string in Eastern Time, e.g. "Wednesday, February 04, 2026".
    var estFormatted: String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = Self.easternTimeZone
        formatter.dateFormat = "EEEE, MMMM dd, yyyy"
        return formatter.string(from: self)
    }

    /// Time string in Eastern Time, e.g. "3:45 PM EST" or "3:45 PM EDT".
    var estTime: String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = Self.easternTimeZone
        formatter.dateFormat = "h:mm a zzz"
        return formatter.string(from: self)
    }

    // MARK: - Market Hours

    /// `true` when the date falls on a weekday between 9:30 AM and 4:00 PM Eastern Time.
    ///
    /// > Note: This does **not** account for US stock-market holidays.
    var isMarketHours: Bool {
        let cal = Self.easternCalendar
        let weekday = cal.component(.weekday, from: self)

        // 1 = Sunday, 7 = Saturday
        guard (2...6).contains(weekday) else { return false }

        let hour = cal.component(.hour, from: self)
        let minute = cal.component(.minute, from: self)
        let totalMinutes = hour * 60 + minute

        let marketOpen = 9 * 60 + 30   // 09:30
        let marketClose = 16 * 60       // 16:00

        return totalMinutes >= marketOpen && totalMinutes < marketClose
    }

    /// Human-readable market status label based on Eastern Time:
    /// - **"Market Open"** -- Mon-Fri 9:30 AM - 4:00 PM ET
    /// - **"Pre-Market"** -- Mon-Fri 4:00 AM - 9:30 AM ET
    /// - **"After Hours"** -- Mon-Fri 4:00 PM - 8:00 PM ET
    /// - **"Market Closed"** -- all other times (overnight, weekends)
    var marketStatusLabel: String {
        let cal = Self.easternCalendar
        let weekday = cal.component(.weekday, from: self)

        // Weekends
        guard (2...6).contains(weekday) else { return "Market Closed" }

        let hour = cal.component(.hour, from: self)
        let minute = cal.component(.minute, from: self)
        let totalMinutes = hour * 60 + minute

        let preMarketOpen = 4 * 60      // 04:00
        let marketOpen    = 9 * 60 + 30 // 09:30
        let marketClose   = 16 * 60     // 16:00
        let afterClose    = 20 * 60     // 20:00

        if totalMinutes >= marketOpen && totalMinutes < marketClose {
            return "Market Open"
        } else if totalMinutes >= preMarketOpen && totalMinutes < marketOpen {
            return "Pre-Market"
        } else if totalMinutes >= marketClose && totalMinutes < afterClose {
            return "After Hours"
        } else {
            return "Market Closed"
        }
    }
}
