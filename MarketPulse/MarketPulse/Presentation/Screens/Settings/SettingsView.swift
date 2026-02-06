import SwiftUI

/// Main settings screen with NavigationStack and grouped sections.
struct SettingsView: View {
    @State private var viewModel = SettingsViewModel()

    var body: some View {
        NavigationStack {
            List {
                // API Keys
                Section {
                    NavigationLink {
                        APIKeysSettingsView(viewModel: viewModel)
                    } label: {
                        Label("API Keys", systemImage: "key.fill")
                    }
                } header: {
                    Text("Data Sources")
                } footer: {
                    if viewModel.hasRequiredKeys {
                        Label("All required keys configured", systemImage: "checkmark.circle")
                            .foregroundStyle(MPColor.gain)
                            .font(MPFont.caption())
                    } else {
                        Label("Missing required API keys", systemImage: "exclamationmark.triangle")
                            .foregroundStyle(MPColor.loss)
                            .font(MPFont.caption())
                    }
                }

                // AI Provider
                Section {
                    NavigationLink {
                        AIProviderSettingsView(viewModel: viewModel)
                    } label: {
                        HStack {
                            Label("AI Provider", systemImage: "sparkles")
                            Spacer()
                            Text(viewModel.selectedAIProvider.rawValue)
                                .font(MPFont.caption())
                                .foregroundStyle(MPColor.textTertiary)
                        }
                    }
                } header: {
                    Text("Analysis")
                }

                // Refresh Settings
                Section {
                    NavigationLink {
                        RefreshSettingsView(viewModel: viewModel)
                    } label: {
                        HStack {
                            Label("Auto-Refresh", systemImage: "arrow.clockwise")
                            Spacer()
                            Text(viewModel.autoRefresh ? "Every \(viewModel.refreshMinutes) min" : "Off")
                                .font(MPFont.caption())
                                .foregroundStyle(MPColor.textTertiary)
                        }
                    }
                } header: {
                    Text("Schedule")
                }

                // About
                Section {
                    HStack {
                        Text("Version")
                        Spacer()
                        Text(appVersion)
                            .foregroundStyle(MPColor.textTertiary)
                    }

                    HStack {
                        Text("Build")
                        Spacer()
                        Text(appBuild)
                            .foregroundStyle(MPColor.textTertiary)
                    }
                } header: {
                    Text("About")
                } footer: {
                    Text("MarketPulse - Daily Market Scanner")
                        .font(MPFont.caption())
                        .foregroundStyle(MPColor.textTertiary)
                        .frame(maxWidth: .infinity)
                        .padding(.top, MPSpacing.card)
                }
            }
            .navigationTitle("Settings")
            .scrollContentBackground(.hidden)
            .background(MPColor.background)
        }
    }

    // MARK: - App Info

    private var appVersion: String {
        Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0.0"
    }

    private var appBuild: String {
        Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "1"
    }
}

#Preview {
    SettingsView()
        .preferredColorScheme(.dark)
}
