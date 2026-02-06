import Foundation

/// Analyzes sector rotation data to identify the hottest and coldest sectors
/// and produces a human-readable rotation notes string.
struct AnalyzeSectorRotationUseCase: Sendable {

    func analyze(
        _ sectors: [SectorRotation]
    ) -> (hot: [SectorRotation], cold: [SectorRotation], notes: String) {

        let hot = sectors
            .filter { $0.changePercent > 1.0 }
            .sorted { $0.changePercent > $1.changePercent }
            .prefix(3)

        let cold = sectors
            .filter { $0.changePercent < -1.0 }
            .sorted { $0.changePercent < $1.changePercent }
            .prefix(3)

        let notes = buildNotes(hot: Array(hot), cold: Array(cold))

        return (hot: Array(hot), cold: Array(cold), notes: notes)
    }

    // MARK: - Private

    private func buildNotes(
        hot: [SectorRotation],
        cold: [SectorRotation]
    ) -> String {
        var parts: [String] = []

        if !hot.isEmpty {
            let names = hot.map { "\($0.name) (+\(formatted($0.changePercent))%)" }
            parts.append("Money rotating into \(names.joined(separator: ", ")).")
        }

        if !cold.isEmpty {
            let names = cold.map { "\($0.name) (\(formatted($0.changePercent))%)" }
            parts.append("Weakness in \(names.joined(separator: ", ")).")
        }

        if hot.isEmpty, cold.isEmpty {
            parts.append("No significant sector rotation detected today.")
        }

        return parts.joined(separator: " ")
    }

    private func formatted(_ value: Double) -> String {
        String(format: "%.1f", value)
    }
}
