import Foundation

/// System and user prompt templates for AI-powered market scan generation.
///
/// All prompts target the FINVIZ-style 12-section scan output format used
/// throughout the MarketPulse app.
enum PromptTemplates {

    // MARK: - System Prompts

    /// System prompt for generating a Quick Take summary paragraph.
    static let quickTakeSystem: String = """
        You are a senior equity market analyst writing a concise daily market summary \
        for active traders. Your output is a single paragraph (3-5 sentences) that \
        captures the day's most important theme, key movers, and actionable outlook. \
        Use a professional yet direct tone. Reference specific tickers with the \
        $TICKER format. Include percentages to exactly 2 decimal places. Do not use \
        headers, bullet points, or section labels -- only a plain paragraph.
        """

    /// System prompt for generating a full 12-section formatted scan report.
    static let fullScanSystem: String = """
        You are a senior equity market analyst producing a structured daily market \
        scan report for active traders. You MUST output EXACTLY the following sections \
        in order, using the specified headers and emoji. Every section header must be \
        in ALL CAPS. Use consistent bullet points (- ) for list items. Format all \
        tickers as $TICKER. Format all percentages to exactly 2 decimal places. \
        Do not add any sections beyond those listed below. The report MUST end with \
        the line "End scan." on its own line.

        Required format:

        MARKET SENTIMENT: {emoji} {Bullish|Bearish|Neutral}
        INDEX SNAPSHOT: {ticker}: {price} ({changePercent}%) ...
        \u{1F4C8} MARKET MOVES:
        - ${TICKER} {surges|drops} {changePercent}% ...
        \u{1F3E2} CORPORATE:
        - {headline with $TICKER references}
        \u{1F30E} MACRO:
        - {headline}
        \u{1F4CA} SECTOR ROTATION:
        \u{1F525} HOT:
        - {sector}: {changePercent}% (led by $TICKER, $TICKER)
        \u{2744}\u{FE0F} COLD:
        - {sector}: {changePercent}% (dragged by $TICKER, $TICKER)
        \u{1F4CC} ROTATION NOTES:
        {1-2 sentence rotation analysis}
        \u{1F4E2} VOLUME SIGNALS:
        - $TICKER: {volume} ({volumeRatio}x avg) -- {reason}
        \u{1F4A1} KEY TICKERS:
        - $TICKER: {price} ({changePercent}%) -- {note}
        \u{26A1} QUICK TAKE:
        {3-5 sentence market summary paragraph}
        \u{1F440} WATCH LIST:
        - $TICKER -- {reason}

        End scan.
        """

    /// System prompt for generating sector rotation analysis notes.
    static let rotationNotesSystem: String = """
        You are a senior equity market analyst specializing in sector rotation \
        analysis. Given lists of hot (gaining) and cold (losing) sectors with their \
        performance data, write 1-2 concise sentences explaining the rotation theme. \
        Reference specific sector names and mention leading tickers using $TICKER \
        format. Percentages must be to exactly 2 decimal places. Output only the \
        analysis text with no headers or bullet points.
        """

    // MARK: - User Prompt Builders

    /// Build the user prompt for Quick Take generation from a completed scan.
    ///
    /// - Parameter scan: The fully populated `MarketScan`.
    /// - Returns: A formatted user prompt string containing all scan data.
    static func buildQuickTakeUserPrompt(from scan: MarketScan) -> String {
        var parts: [String] = []

        parts.append("Generate a Quick Take paragraph for the following market data:")
        parts.append("")

        // Sentiment
        parts.append("Sentiment: \(scan.sentiment.emoji) \(scan.sentiment.label)")
        parts.append("")

        // Index snapshots
        parts.append("Index Snapshots:")
        for index in scan.indexSnapshots {
            let sign = index.changePercent >= 0 ? "+" : ""
            parts.append("- \(index.name): \(String(format: "%.2f", index.price)) (\(sign)\(String(format: "%.2f", index.changePercent))%)")
        }
        parts.append("")

        // Top gainers
        if !scan.topGainers.isEmpty {
            parts.append("Top Gainers:")
            for mover in scan.topGainers {
                parts.append("- $\(mover.ticker): \(String(format: "+%.2f", mover.changePercent))% (vol \(mover.volume.asVolume))")
            }
            parts.append("")
        }

        // Top losers
        if !scan.topLosers.isEmpty {
            parts.append("Top Losers:")
            for mover in scan.topLosers {
                parts.append("- $\(mover.ticker): \(String(format: "%.2f", mover.changePercent))% (vol \(mover.volume.asVolume))")
            }
            parts.append("")
        }

        // Corporate news
        if !scan.corporateNews.isEmpty {
            parts.append("Corporate Headlines:")
            for news in scan.corporateNews.prefix(5) {
                let ticker = news.ticker.map { " ($\($0))" } ?? ""
                parts.append("- \(news.headline)\(ticker)")
            }
            parts.append("")
        }

        // Macro news
        if !scan.macroNews.isEmpty {
            parts.append("Macro Headlines:")
            for news in scan.macroNews.prefix(5) {
                parts.append("- \(news.headline)")
            }
            parts.append("")
        }

        // Sector rotation
        if !scan.hotSectors.isEmpty {
            parts.append("Hot Sectors:")
            for sector in scan.hotSectors {
                let tickers = sector.leadingTickers.map { "$\($0)" }.joined(separator: ", ")
                parts.append("- \(sector.name): \(String(format: "+%.2f", sector.changePercent))% (led by \(tickers))")
            }
            parts.append("")
        }

        if !scan.coldSectors.isEmpty {
            parts.append("Cold Sectors:")
            for sector in scan.coldSectors {
                let tickers = sector.leadingTickers.map { "$\($0)" }.joined(separator: ", ")
                parts.append("- \(sector.name): \(String(format: "%.2f", sector.changePercent))% (dragged by \(tickers))")
            }
            parts.append("")
        }

        // Volume signals
        if !scan.volumeSignals.isEmpty {
            parts.append("Volume Signals:")
            for signal in scan.volumeSignals {
                parts.append("- $\(signal.ticker): \(signal.volumeFormatted) (\(String(format: "%.1f", signal.volumeRatio))x avg) -- \(signal.reason)")
            }
            parts.append("")
        }

        // Key tickers
        if !scan.keyTickers.isEmpty {
            parts.append("Key Tickers:")
            for ticker in scan.keyTickers {
                let sign = ticker.changePercent >= 0 ? "+" : ""
                let note = ticker.note.map { " -- \($0)" } ?? ""
                parts.append("- $\(ticker.ticker): \(String(format: "%.2f", ticker.price)) (\(sign)\(String(format: "%.2f", ticker.changePercent))%)\(note)")
            }
            parts.append("")
        }

        // Watch list
        if !scan.watchList.isEmpty {
            parts.append("Watch List:")
            for item in scan.watchList {
                parts.append("- $\(item.ticker) -- \(item.reason)")
            }
            parts.append("")
        }

        return parts.joined(separator: "\n")
    }

    /// Build the user prompt for full 12-section scan generation from a completed scan.
    ///
    /// - Parameter scan: The fully populated `MarketScan`.
    /// - Returns: A formatted user prompt string containing all scan data.
    static func buildFullScanUserPrompt(from scan: MarketScan) -> String {
        var parts: [String] = []

        parts.append("Generate the full 12-section market scan report from the following data.")
        parts.append("Follow the exact section format from your system instructions.")
        parts.append("Date: \(scan.generatedAt.estFormatted) (\(scan.generatedAt.estTime))")
        parts.append("")

        // Sentiment
        parts.append("Overall Sentiment: \(scan.sentiment.rawValue)")
        parts.append("")

        // Index snapshots
        parts.append("INDEX DATA:")
        for index in scan.indexSnapshots {
            let sign = index.changePercent >= 0 ? "+" : ""
            parts.append("  \(index.name) (\(index.id)): price=\(String(format: "%.2f", index.price)), change=\(sign)\(String(format: "%.2f", index.change)), pct=\(sign)\(String(format: "%.2f", index.changePercent))%")
        }
        parts.append("")

        // Market movers - gainers
        parts.append("TOP GAINERS:")
        for mover in scan.topGainers {
            let sector = mover.sector ?? "N/A"
            parts.append("  $\(mover.ticker) (\(mover.companyName)): \(String(format: "+%.2f", mover.changePercent))%, price=\(String(format: "%.2f", mover.price)), vol=\(mover.volume.asVolume), avgVol=\(mover.averageVolume.asVolume), sector=\(sector)")
        }
        parts.append("")

        // Market movers - losers
        parts.append("TOP LOSERS:")
        for mover in scan.topLosers {
            let sector = mover.sector ?? "N/A"
            parts.append("  $\(mover.ticker) (\(mover.companyName)): \(String(format: "%.2f", mover.changePercent))%, price=\(String(format: "%.2f", mover.price)), vol=\(mover.volume.asVolume), avgVol=\(mover.averageVolume.asVolume), sector=\(sector)")
        }
        parts.append("")

        // Corporate news
        parts.append("CORPORATE NEWS:")
        for news in scan.corporateNews {
            let ticker = news.ticker.map { " [$\($0)]" } ?? ""
            parts.append("  - \(news.headline)\(ticker) (via \(news.source))")
        }
        parts.append("")

        // Macro news
        parts.append("MACRO NEWS:")
        for news in scan.macroNews {
            parts.append("  - \(news.headline) (via \(news.source))")
        }
        parts.append("")

        // Sector rotation
        parts.append("SECTOR ROTATION:")
        parts.append("  Hot:")
        for sector in scan.hotSectors {
            let tickers = sector.leadingTickers.map { "$\($0)" }.joined(separator: ", ")
            parts.append("    \(sector.name): \(String(format: "+%.2f", sector.changePercent))% (leaders: \(tickers))")
        }
        parts.append("  Cold:")
        for sector in scan.coldSectors {
            let tickers = sector.leadingTickers.map { "$\($0)" }.joined(separator: ", ")
            parts.append("    \(sector.name): \(String(format: "%.2f", sector.changePercent))% (laggards: \(tickers))")
        }
        parts.append("")

        // Existing rotation notes (if any)
        if !scan.rotationNotes.isEmpty {
            parts.append("EXISTING ROTATION NOTES: \(scan.rotationNotes)")
            parts.append("")
        }

        // Volume signals
        parts.append("VOLUME SIGNALS:")
        for signal in scan.volumeSignals {
            let sign = signal.changePercent >= 0 ? "+" : ""
            parts.append("  $\(signal.ticker): vol=\(signal.volumeFormatted), ratio=\(String(format: "%.1f", signal.volumeRatio))x, pct=\(sign)\(String(format: "%.2f", signal.changePercent))%, reason=\(signal.reason)")
        }
        parts.append("")

        // Key tickers
        parts.append("KEY TICKERS:")
        for ticker in scan.keyTickers {
            let sign = ticker.changePercent >= 0 ? "+" : ""
            let note = ticker.note ?? "N/A"
            parts.append("  $\(ticker.ticker): price=\(String(format: "%.2f", ticker.price)), pct=\(sign)\(String(format: "%.2f", ticker.changePercent))%, note=\(note)")
        }
        parts.append("")

        // Watch list
        parts.append("WATCH LIST:")
        for item in scan.watchList {
            parts.append("  $\(item.ticker): \(item.reason)")
        }
        parts.append("")

        parts.append("Produce the complete formatted report now. End with \"End scan.\"")

        return parts.joined(separator: "\n")
    }

    /// Build the user prompt for sector rotation notes generation.
    ///
    /// - Parameters:
    ///   - hot: Sectors with positive rotation.
    ///   - cold: Sectors with negative rotation.
    /// - Returns: A formatted user prompt string with sector data.
    static func buildRotationNotesPrompt(hot: [SectorRotation], cold: [SectorRotation]) -> String {
        var parts: [String] = []

        parts.append("Analyze the following sector rotation data and write 1-2 sentences:")
        parts.append("")

        if !hot.isEmpty {
            parts.append("HOT (gaining) sectors:")
            for sector in hot {
                let tickers = sector.leadingTickers.map { "$\($0)" }.joined(separator: ", ")
                parts.append("- \(sector.name): \(String(format: "+%.2f", sector.changePercent))% (leading tickers: \(tickers))")
            }
            parts.append("")
        } else {
            parts.append("HOT sectors: None today.")
            parts.append("")
        }

        if !cold.isEmpty {
            parts.append("COLD (losing) sectors:")
            for sector in cold {
                let tickers = sector.leadingTickers.map { "$\($0)" }.joined(separator: ", ")
                parts.append("- \(sector.name): \(String(format: "%.2f", sector.changePercent))% (lagging tickers: \(tickers))")
            }
        } else {
            parts.append("COLD sectors: None today.")
        }

        return parts.joined(separator: "\n")
    }
}
