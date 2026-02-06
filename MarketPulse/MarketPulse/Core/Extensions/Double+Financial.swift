import Foundation

extension Double {

    // MARK: - Currency

    /// Full currency string, e.g. "$1,234.56". Negative values show as "-$1,234.56".
    var asCurrency: String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = "USD"
        formatter.currencySymbol = "$"
        formatter.locale = Locale(identifier: "en_US")
        formatter.minimumFractionDigits = 2
        formatter.maximumFractionDigits = 2
        return formatter.string(from: NSNumber(value: self)) ?? "$0.00"
    }

    /// Compact currency string with magnitude suffix:
    /// - >= 1 trillion  -> "$1.2T"
    /// - >= 1 billion   -> "$1.2B"
    /// - >= 1 million   -> "$45.3M"
    /// - >= 1 thousand  -> "$12.5K"
    /// - otherwise      -> "$123.45"
    var asCompactCurrency: String {
        let absValue = abs(self)
        let sign = self < 0 ? "-" : ""

        switch absValue {
        case 1_000_000_000_000...:
            return "\(sign)$\(Self.compactString(absValue / 1_000_000_000_000))T"
        case 1_000_000_000...:
            return "\(sign)$\(Self.compactString(absValue / 1_000_000_000))B"
        case 1_000_000...:
            return "\(sign)$\(Self.compactString(absValue / 1_000_000))M"
        case 1_000...:
            return "\(sign)$\(Self.compactString(absValue / 1_000))K"
        default:
            let formatter = NumberFormatter()
            formatter.numberStyle = .decimal
            formatter.locale = Locale(identifier: "en_US")
            formatter.minimumFractionDigits = 2
            formatter.maximumFractionDigits = 2
            return "\(sign)$\(formatter.string(from: NSNumber(value: absValue)) ?? "0.00")"
        }
    }

    // MARK: - Percentage

    /// Signed percentage string with exactly 2 decimal places: "+1.23%" or "-1.23%".
    /// Zero displays as "+0.00%".
    var asPercentage: String {
        let sign: String
        if self > 0 {
            sign = "+"
        } else if self < 0 {
            sign = ""  // negative sign is included by the formatter
        } else {
            sign = "+"
        }

        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        formatter.locale = Locale(identifier: "en_US")
        formatter.minimumFractionDigits = 2
        formatter.maximumFractionDigits = 2
        let formatted = formatter.string(from: NSNumber(value: self)) ?? "0.00"
        return "\(sign)\(formatted)%"
    }

    // MARK: - Volume

    /// Compact volume string without currency symbol:
    /// - >= 1 billion   -> "1.2B"
    /// - >= 1 million   -> "51.8M"
    /// - >= 1 thousand  -> "450K"
    /// - otherwise      -> "123"
    var asVolume: String {
        let absValue = abs(self)
        let sign = self < 0 ? "-" : ""

        switch absValue {
        case 1_000_000_000...:
            return "\(sign)\(Self.compactString(absValue / 1_000_000_000))B"
        case 1_000_000...:
            return "\(sign)\(Self.compactString(absValue / 1_000_000))M"
        case 1_000...:
            return "\(sign)\(Self.compactString(absValue / 1_000))K"
        default:
            let formatter = NumberFormatter()
            formatter.numberStyle = .decimal
            formatter.locale = Locale(identifier: "en_US")
            formatter.maximumFractionDigits = 0
            return "\(sign)\(formatter.string(from: NSNumber(value: absValue)) ?? "0")"
        }
    }

    // MARK: - Sign

    /// Returns "+" for positive values, "-" for negative, and "" for zero.
    var gainLossSign: String {
        if self > 0 { return "+" }
        if self < 0 { return "-" }
        return ""
    }

    // MARK: - Private Helpers

    /// Formats a value with up to 1 decimal place, dropping ".0" when whole.
    private static func compactString(_ value: Double) -> String {
        if value >= 100 {
            // Large magnitudes: show as integer to keep it compact.
            return String(format: "%.0f", value)
        } else if value == value.rounded(.down) {
            // Whole number: skip the decimal.
            return String(format: "%.0f", value)
        } else {
            return String(format: "%.1f", value)
        }
    }
}
