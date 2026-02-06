import SwiftUI

/// Segmented picker for selecting AI provider: Claude API vs Apple Intelligence.
struct AIProviderSettingsView: View {
    @Bindable var viewModel: SettingsViewModel

    var body: some View {
        Form {
            Section {
                Picker("AI Provider", selection: $viewModel.selectedAIProvider) {
                    ForEach(SettingsViewModel.AIProvider.allCases, id: \.self) { provider in
                        Text(provider.rawValue).tag(provider)
                    }
                }
                .pickerStyle(.segmented)
            } header: {
                Label("Provider", systemImage: "sparkles")
            }

            // Description for selected provider
            Section {
                switch viewModel.selectedAIProvider {
                case .claude:
                    claudeDescription
                case .appleIntelligence:
                    appleIntelligenceDescription
                }
            } header: {
                Text("Details")
            }
        }
        .navigationTitle("AI Provider")
        .navigationBarTitleDisplayMode(.inline)
        .scrollContentBackground(.hidden)
        .background(MPColor.background)
        .onChange(of: viewModel.selectedAIProvider) { _, newValue in
            // Fall back to Claude if Apple Intelligence is not available.
            if newValue == .appleIntelligence && !viewModel.isAppleIntelligenceAvailable {
                viewModel.selectedAIProvider = .claude
            }
        }
    }

    // MARK: - Provider Descriptions

    private var claudeDescription: some View {
        VStack(alignment: .leading, spacing: MPSpacing.item) {
            HStack(spacing: MPSpacing.item) {
                Image(systemName: "brain.head.profile.fill")
                    .foregroundStyle(MPColor.accent)
                Text("Claude API")
                    .font(MPFont.sectionTitle())
                    .foregroundStyle(MPColor.textPrimary)
            }

            Text("Uses Anthropic's Claude model via the Messages API to generate Quick Take analysis. Requires a valid Claude API key. Provides high-quality financial analysis with nuanced market commentary.")
                .font(MPFont.body())
                .foregroundStyle(MPColor.textSecondary)

            if viewModel.claudeApiKey.isEmpty {
                Label("API key not configured", systemImage: "exclamationmark.triangle.fill")
                    .font(MPFont.caption())
                    .foregroundStyle(MPColor.loss)
            } else {
                Label("API key configured", systemImage: "checkmark.circle.fill")
                    .font(MPFont.caption())
                    .foregroundStyle(MPColor.gain)
            }
        }
    }

    private var appleIntelligenceDescription: some View {
        VStack(alignment: .leading, spacing: MPSpacing.item) {
            HStack(spacing: MPSpacing.item) {
                Image(systemName: "apple.logo")
                    .foregroundStyle(MPColor.textPrimary)
                Text("Apple Intelligence")
                    .font(MPFont.sectionTitle())
                    .foregroundStyle(MPColor.textPrimary)
            }

            Text("Uses on-device Foundation Models (iOS 26+) for private, zero-cost analysis. Summaries are generated entirely on your device with no data leaving the phone.")
                .font(MPFont.body())
                .foregroundStyle(MPColor.textSecondary)

            if viewModel.isAppleIntelligenceAvailable {
                Label("Available on this device", systemImage: "checkmark.circle.fill")
                    .font(MPFont.caption())
                    .foregroundStyle(MPColor.gain)
            } else {
                Label("Not available - requires iOS 26+ on a supported device", systemImage: "xmark.circle.fill")
                    .font(MPFont.caption())
                    .foregroundStyle(MPColor.loss)
            }
        }
    }
}

#Preview {
    NavigationStack {
        AIProviderSettingsView(viewModel: SettingsViewModel())
    }
    .preferredColorScheme(.dark)
}
