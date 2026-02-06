import Foundation

// MARK: - Protocol

/// Minimal HTTP client abstraction for testability.
protocol HTTPClientProtocol: Sendable {
    /// Performs an HTTP GET request.
    ///
    /// - Parameters:
    ///   - url: The endpoint URL.
    ///   - headers: Additional HTTP headers to include.
    /// - Returns: The raw response body.
    /// - Throws: `MarketPulseError.networkError` for non-2xx status codes.
    func fetch(url: URL, headers: [String: String]) async throws -> Data

    /// Performs an HTTP POST request.
    ///
    /// - Parameters:
    ///   - url: The endpoint URL.
    ///   - headers: Additional HTTP headers to include.
    ///   - body: The request body data.
    /// - Returns: The raw response body.
    /// - Throws: `MarketPulseError.networkError` for non-2xx status codes.
    func post(url: URL, headers: [String: String], body: Data) async throws -> Data
}

// MARK: - URLSession Implementation

/// Production HTTP client backed by `URLSession`.
struct URLSessionHTTPClient: HTTPClientProtocol {

    /// The underlying session. Injected for testability; defaults to `.shared`.
    private let session: URLSession

    /// Custom User-Agent header value.
    private static let userAgent = "MarketPulse/1.0 (iOS; Swift)"

    init(session: URLSession = .shared) {
        self.session = session
    }

    // MARK: - HTTPClientProtocol

    func fetch(url: URL, headers: [String: String] = [:]) async throws -> Data {
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        applyHeaders(&request, headers)
        return try await execute(request)
    }

    func post(url: URL, headers: [String: String] = [:], body: Data) async throws -> Data {
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.httpBody = body
        applyHeaders(&request, headers)
        return try await execute(request)
    }

    // MARK: - Private

    /// Applies default and caller-supplied headers to a request.
    private func applyHeaders(_ request: inout URLRequest, _ headers: [String: String]) {
        request.setValue(Self.userAgent, forHTTPHeaderField: "User-Agent")
        for (key, value) in headers {
            request.setValue(value, forHTTPHeaderField: key)
        }
    }

    /// Executes a `URLRequest`, validates the HTTP status code, and returns the body.
    private func execute(_ request: URLRequest) async throws -> Data {
        let (data, response): (Data, URLResponse)

        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw MarketPulseError.networkError(
                statusCode: 0,
                message: error.localizedDescription
            )
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw MarketPulseError.networkError(
                statusCode: 0,
                message: "Response is not an HTTP response."
            )
        }

        let statusCode = httpResponse.statusCode

        guard (200...299).contains(statusCode) else {
            // Attempt to surface a human-readable message from the body.
            let bodyMessage = String(data: data, encoding: .utf8)
            let truncated = bodyMessage.map { String($0.prefix(500)) }

            if statusCode == 429 {
                throw MarketPulseError.rateLimitExceeded
            }

            throw MarketPulseError.networkError(
                statusCode: statusCode,
                message: truncated
            )
        }

        return data
    }
}
