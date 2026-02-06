import Foundation

/// Maps the JSON response from Finnhub `GET /quote`.
///
/// Field key reference (Finnhub API):
/// - `c`  : current price
/// - `d`  : change (absolute)
/// - `dp` : change percent
/// - `h`  : day high
/// - `l`  : day low
/// - `o`  : open price
/// - `pc` : previous close
/// - `t`  : UNIX timestamp
struct FinnhubQuoteDTO: Codable, Sendable {
    let c: Double
    let d: Double
    let dp: Double
    let h: Double
    let l: Double
    let o: Double
    let pc: Double
    let t: Int
}
