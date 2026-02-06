import Foundation

/// A token-bucket rate limiter that restricts the number of requests per minute.
///
/// Usage:
/// ```swift
/// let limiter = RateLimiter(maxRequestsPerMinute: 30)
/// await limiter.acquire()   // blocks until a token is available
/// // ... make request ...
/// ```
///
/// Tokens refill continuously at a rate of `maxRequestsPerMinute / 60` tokens
/// per second, up to the configured maximum burst size.
actor RateLimiter {

    // MARK: - Configuration

    /// Maximum number of tokens the bucket can hold (burst size).
    private let maxTokens: Double

    /// Tokens added per second.
    private let refillRate: Double

    // MARK: - State

    /// Current number of available tokens.
    private var availableTokens: Double

    /// The last time tokens were refilled.
    private var lastRefill: ContinuousClock.Instant

    // MARK: - Init

    /// Creates a rate limiter that permits at most `maxRequestsPerMinute`
    /// requests in any sliding 60-second window.
    ///
    /// - Parameter maxRequestsPerMinute: The sustained request rate.
    ///   Must be greater than zero.
    init(maxRequestsPerMinute: Int) {
        precondition(maxRequestsPerMinute > 0, "maxRequestsPerMinute must be > 0")

        let max = Double(maxRequestsPerMinute)
        self.maxTokens = max
        self.refillRate = max / 60.0
        self.availableTokens = max
        self.lastRefill = .now
    }

    // MARK: - Public API

    /// Acquires a single token, suspending the caller until one is available.
    ///
    /// When the bucket is empty, the method calculates the exact duration
    /// until the next token is produced, sleeps for that interval, and
    /// then retries. This avoids busy-waiting while still being responsive.
    func acquire() async {
        while true {
            refillTokens()

            if availableTokens >= 1.0 {
                availableTokens -= 1.0
                return
            }

            // Calculate time until at least one token is available.
            let deficit = 1.0 - availableTokens
            let waitSeconds = deficit / refillRate

            // Sleep outside the actor to avoid blocking other callers
            // that may only need state queries.
            let duration = Duration.milliseconds(Int(waitSeconds * 1_000) + 1)
            try? await Task.sleep(for: duration)
        }
    }

    // MARK: - Private

    /// Refills tokens based on elapsed time since the last refill,
    /// capping at `maxTokens`.
    private mutating func refillTokens() {
        let now = ContinuousClock.Instant.now
        let elapsed = now - lastRefill
        let elapsedSeconds = Double(elapsed.components.seconds)
            + Double(elapsed.components.attoseconds) / 1e18

        let newTokens = elapsedSeconds * refillRate
        availableTokens = min(maxTokens, availableTokens + newTokens)
        lastRefill = now
    }
}
