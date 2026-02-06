import SwiftUI

/// Root tab view with 2 tabs: Daily Scan and Settings.
/// Dark themed tab bar matching the financial trading aesthetic.
struct AppTabView: View {
    @State private var selectedTab: Tab = .scan

    /// The ViewModel for the Daily Scan tab, injected from the composition root.
    let scanViewModel: DailyScanViewModel

    enum Tab: Hashable {
        case scan
        case settings
    }

    var body: some View {
        TabView(selection: $selectedTab) {
            // Tab 1: Daily Scan
            DailyScanView(viewModel: scanViewModel)
                .tabItem {
                    Label("Scan", systemImage: "chart.bar.fill")
                }
                .tag(Tab.scan)

            // Tab 2: Settings
            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gearshape.fill")
                }
                .tag(Tab.settings)
        }
        .tint(MPColor.accent)
        .onAppear {
            configureTabBarAppearance()
        }
    }

    // MARK: - Tab Bar Appearance

    private func configureTabBarAppearance() {
        let appearance = UITabBarAppearance()
        appearance.configureWithOpaqueBackground()

        // Background color matching the dark theme
        appearance.backgroundColor = UIColor(MPColor.cardBackground)

        // Unselected item color
        let normalAttributes: [NSAttributedString.Key: Any] = [
            .foregroundColor: UIColor(MPColor.textTertiary),
        ]
        appearance.stackedLayoutAppearance.normal.iconColor = UIColor(MPColor.textTertiary)
        appearance.stackedLayoutAppearance.normal.titleTextAttributes = normalAttributes

        // Selected item color
        let selectedAttributes: [NSAttributedString.Key: Any] = [
            .foregroundColor: UIColor(MPColor.accent),
        ]
        appearance.stackedLayoutAppearance.selected.iconColor = UIColor(MPColor.accent)
        appearance.stackedLayoutAppearance.selected.titleTextAttributes = selectedAttributes

        UITabBar.appearance().standardAppearance = appearance
        UITabBar.appearance().scrollEdgeAppearance = appearance
    }
}

#Preview {
    let vm = DailyScanViewModel {
        // Placeholder for preview
        throw MarketPulseError.apiKeyMissing("Preview")
    }

    AppTabView(scanViewModel: vm)
        .preferredColorScheme(.dark)
}
