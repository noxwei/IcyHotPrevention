import AppIntents

/// Registers MarketPulse App Shortcuts with Siri so users can invoke them
/// by voice or from the Shortcuts app without manual setup.
struct TickerLookupShortcutProvider: AppShortcutsProvider {

    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: TickerLookupIntent(),
            phrases: [
                "Look up \(\.$ticker) in \(.applicationName)",
                "Check \(\.$ticker) price in \(.applicationName)",
                "\(.applicationName) quote for \(\.$ticker)"
            ],
            shortTitle: "Stock Lookup",
            systemImageName: "chart.line.uptrend.xyaxis"
        )

        AppShortcut(
            intent: DailyScanIntent(),
            phrases: [
                "Get market pulse from \(.applicationName)",
                "Run daily scan in \(.applicationName)",
                "\(.applicationName) market summary"
            ],
            shortTitle: "Daily Scan",
            systemImageName: "chart.bar.fill"
        )
    }
}
