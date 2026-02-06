import Foundation

extension String {

    /// Unescapes a single CSV field value:
    /// - Removes surrounding quotes if present.
    /// - Replaces doubled double-quotes (`""`) with a single double-quote (`"`).
    var csvUnescaped: String {
        var field = self

        // Trim leading/trailing whitespace outside quotes.
        field = field.trimmingCharacters(in: .whitespaces)

        guard field.hasPrefix("\"") && field.hasSuffix("\"") && field.count >= 2 else {
            return field
        }

        // Strip surrounding quotes.
        field = String(field.dropFirst().dropLast())

        // Un-double any escaped quotes.
        field = field.replacingOccurrences(of: "\"\"", with: "\"")

        return field
    }

    /// Splits a CSV row into individual field strings, correctly handling:
    /// - Quoted fields that contain the separator character.
    /// - Doubled double-quotes inside quoted fields.
    /// - Fields with embedded newlines inside quotes (the caller must supply
    ///   the complete logical row).
    ///
    /// - Parameter separator: The delimiter character (typically `,`).
    /// - Returns: An array of raw (still-escaped) field strings.
    ///   Call `.csvUnescaped` on each element to get the clean value.
    func csvComponents(separator: Character = ",") -> [String] {
        var fields: [String] = []
        var current = ""
        var insideQuotes = false
        var index = self.startIndex

        while index < self.endIndex {
            let char = self[index]

            if insideQuotes {
                if char == "\"" {
                    let next = self.index(after: index)
                    if next < self.endIndex && self[next] == "\"" {
                        // Escaped double-quote inside a quoted field.
                        current.append("\"\"")
                        index = self.index(after: next)
                        continue
                    } else {
                        // Closing quote.
                        current.append(char)
                        insideQuotes = false
                    }
                } else {
                    current.append(char)
                }
            } else {
                if char == "\"" {
                    insideQuotes = true
                    current.append(char)
                } else if char == separator {
                    fields.append(current)
                    current = ""
                } else {
                    current.append(char)
                }
            }

            index = self.index(after: index)
        }

        // Append the last field.
        fields.append(current)

        return fields
    }
}
