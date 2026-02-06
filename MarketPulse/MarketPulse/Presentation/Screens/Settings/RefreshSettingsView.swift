import SwiftUI

/// Toggle for auto-refresh and stepper for refresh interval (5-120 minutes).
struct RefreshSettingsView: View {
    @Bindable var viewModel: SettingsViewModel

    var body: some View {
        Form {
            Section {
                Toggle(isOn: $viewModel.autoRefresh) {
                    Label("Auto-Refresh", systemImage: "arrow.clockwise")
                }
                .tint(MPColor.accent)
            } header: {
                Label("Schedule", systemImage: "clock.fill")
            } footer: {
                Text("When enabled, the scan will automatically refresh at the specified interval during market hours.")
            }

            if viewModel.autoRefresh {
                Section {
                    Stepper(
                        value: $viewModel.refreshMinutes,
                        in: 5...120,
                        step: 5
                    ) {
                        HStack {
                            Text("Interval")
                                .foregroundStyle(MPColor.textPrimary)

                            Spacer()

                            Text("\(viewModel.refreshMinutes) min")
                                .font(MPFont.monoMedium())
                                .foregroundStyle(MPColor.accent)
                        }
                    }
                } header: {
                    Text("Refresh Interval")
                } footer: {
                    Text("Choose between 5 and 120 minutes. Shorter intervals consume more API calls.")
                }

                Section {
                    HStack {
                        Text("API Calls / Hour")
                            .foregroundStyle(MPColor.textSecondary)
                        Spacer()
                        Text("\(callsPerHour)")
                            .font(MPFont.monoMedium())
                            .foregroundStyle(estimatedCallColor)
                    }

                    HStack {
                        Text("API Calls / Trading Day")
                            .foregroundStyle(MPColor.textSecondary)
                        Spacer()
                        Text("\(callsPerTradingDay)")
                            .font(MPFont.monoMedium())
                            .foregroundStyle(estimatedCallColor)
                    }
                } header: {
                    Text("Estimated Usage")
                }
            }

            // Save
            Section {
                Button {
                    viewModel.saveToKeychain()
                } label: {
                    HStack {
                        Spacer()
                        Label("Save Settings", systemImage: "checkmark.circle.fill")
                            .font(MPFont.body())
                        Spacer()
                    }
                }
                .tint(MPColor.accent)
            }
        }
        .navigationTitle("Refresh")
        .navigationBarTitleDisplayMode(.inline)
        .scrollContentBackground(.hidden)
        .background(MPColor.background)
    }

    // MARK: - Computed

    private var callsPerHour: Int {
        guard viewModel.refreshMinutes > 0 else { return 0 }
        return 60 / viewModel.refreshMinutes
    }

    private var callsPerTradingDay: Int {
        // Trading day is 6.5 hours (9:30 AM - 4:00 PM)
        guard viewModel.refreshMinutes > 0 else { return 0 }
        return Int(ceil(390.0 / Double(viewModel.refreshMinutes)))
    }

    private var estimatedCallColor: Color {
        switch callsPerHour {
        case 0...4: return MPColor.gain
        case 5...8: return MPColor.hotSector
        default: return MPColor.loss
        }
    }
}

#Preview {
    NavigationStack {
        RefreshSettingsView(viewModel: SettingsViewModel())
    }
    .preferredColorScheme(.dark)
}
