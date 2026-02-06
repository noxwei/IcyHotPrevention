import SwiftUI

@main
struct MarketPulseApp: App {

    @State private var container = AppDependencyContainer()

    var body: some Scene {
        WindowGroup {
            AppTabView(scanViewModel: container.dailyScanViewModel)
                .preferredColorScheme(.dark)
        }
    }
}
