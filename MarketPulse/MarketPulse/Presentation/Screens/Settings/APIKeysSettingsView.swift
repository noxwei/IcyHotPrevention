import SwiftUI

/// Form with SecureFields for FINVIZ token, FINVIZ portfolio ID, Finnhub API key, Claude API key.
struct APIKeysSettingsView: View {
    @Bindable var viewModel: SettingsViewModel

    var body: some View {
        Form {
            // FINVIZ section
            Section {
                SecureField("FINVIZ Token", text: $viewModel.finvizToken)
                    .textContentType(.password)
                    .autocorrectionDisabled()
                    .textInputAutocapitalization(.never)

                TextField("FINVIZ Portfolio ID", text: $viewModel.finvizPortfolioId)
                    .autocorrectionDisabled()
                    .textInputAutocapitalization(.never)
            } header: {
                Label("FINVIZ", systemImage: "chart.bar.fill")
            } footer: {
                Text("Your FINVIZ Elite token and portfolio ID for market screener data.")
            }

            // Finnhub section
            Section {
                SecureField("Finnhub API Key", text: $viewModel.finnhubApiKey)
                    .textContentType(.password)
                    .autocorrectionDisabled()
                    .textInputAutocapitalization(.never)
            } header: {
                Label("Finnhub", systemImage: "network")
            } footer: {
                Text("Free tier provides 60 API calls/minute. Get your key at finnhub.io.")
            }

            // Claude section
            Section {
                SecureField("Claude API Key", text: $viewModel.claudeApiKey)
                    .textContentType(.password)
                    .autocorrectionDisabled()
                    .textInputAutocapitalization(.never)
            } header: {
                Label("Anthropic", systemImage: "brain.head.profile.fill")
            } footer: {
                Text("Required for Claude-powered Quick Take analysis. Get your key at console.anthropic.com.")
            }

            // Save
            Section {
                Button {
                    viewModel.saveToKeychain()
                } label: {
                    HStack {
                        Spacer()
                        Label("Save API Keys", systemImage: "lock.shield.fill")
                            .font(MPFont.body())
                        Spacer()
                    }
                }
                .tint(MPColor.accent)
            }
        }
        .navigationTitle("API Keys")
        .navigationBarTitleDisplayMode(.inline)
        .scrollContentBackground(.hidden)
        .background(MPColor.background)
        .alert("Saved", isPresented: $viewModel.showSaveConfirmation) {
            Button("OK", role: .cancel) { }
        } message: {
            Text("API keys saved securely to Keychain.")
        }
    }
}

#Preview {
    NavigationStack {
        APIKeysSettingsView(viewModel: SettingsViewModel())
    }
    .preferredColorScheme(.dark)
}
