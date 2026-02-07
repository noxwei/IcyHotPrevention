"use client";

import { useState, useEffect } from "react";
import { Search, SlidersHorizontal, X } from "lucide-react";
import {
  MOCK_CONTRACTS,
  MOCK_LEGAL_CASES,
  MOCK_NEWS_EVENTS,
  formatCurrency,
  timeAgo,
} from "@/lib/constants";
import SourceBadge from "@/components/source-badge";
import ConnectedChips from "@/components/connected-chips";

type SourceType = "contracts" | "sec" | "legal" | "news" | "flights";
type FilterType = "all" | SourceType;

const SOURCE_COLORS: Record<SourceType, string> = {
  contracts: "#F59E0B",
  sec: "#4F8EF7",
  legal: "#8B5CF6",
  news: "#10B981",
  flights: "#EF4444",
};

const FILTER_CHIPS: { label: string; value: FilterType }[] = [
  { label: "All", value: "all" },
  { label: "Contracts", value: "contracts" },
  { label: "SEC Filings", value: "sec" },
  { label: "Legal", value: "legal" },
  { label: "News", value: "news" },
  { label: "Flights", value: "flights" },
];

interface SearchResult {
  id: string;
  source: SourceType;
  title: string;
  details: string;
  excerpt: string;
  relevance: number;
  connections: Array<{
    label: string;
    href: string;
    source: SourceType;
  }>;
}

function highlightTerms(text: string, query: string): React.ReactNode {
  if (!query.trim()) return text;

  const terms = query
    .toLowerCase()
    .split(/\s+/)
    .filter((t) => t.length > 2);
  if (terms.length === 0) return text;

  const regex = new RegExp(`(${terms.join("|")})`, "gi");
  const parts = text.split(regex);

  return parts.map((part, i) =>
    terms.some((t) => part.toLowerCase() === t) ? (
      <span
        key={i}
        style={{ color: "var(--accent)", fontWeight: 600 }}
      >
        {part}
      </span>
    ) : (
      part
    )
  );
}

function buildMockResults(): SearchResult[] {
  const contract0 = MOCK_CONTRACTS[0];
  const news0 = MOCK_NEWS_EVENTS[0];

  return [
    {
      id: "result-legal-1",
      source: "legal",
      title: "Doe v. ICE, Case No. 4:24-cv-01234",
      details: "S.D. Texas | Filed Jan 15, 2025 | Deportation (NOS 462)",
      excerpt:
        "Allegations of inadequate medical care and inhumane detention facility conditions at the South Texas Processing Center operated by CoreCivic. Detainees reported overcrowding, insufficient access to legal counsel, and denial of basic hygiene necessities...",
      relevance: 0.94,
      connections: [
        { label: "CoreCivic SEC Filing", href: "#", source: "sec" },
        { label: "Contract HSCE-24-0012", href: "#", source: "contracts" },
      ],
    },
    {
      id: "result-contract-1",
      source: "contracts",
      title: `${contract0.id} - ${contract0.contractor}`,
      details: `${contract0.agency} | FY${contract0.fy} | ${formatCurrency(contract0.amount)}`,
      excerpt: contract0.description,
      relevance: 0.91,
      connections: [
        { label: "Doe v. ICE", href: "#", source: "legal" },
        { label: "CoreCivic 10-K Filing", href: "#", source: "sec" },
      ],
    },
    {
      id: "result-news-1",
      source: "news",
      title: news0.title,
      details: `${news0.source} | ${timeAgo(news0.date)} | Goldstein: ${news0.goldstein} | ${news0.mentions} mentions`,
      excerpt:
        "Multiple organizations have raised concerns about detention facility conditions following a series of inspections. Reports cite inadequate medical staffing, overcrowded dormitories, and lack of proper ventilation in holding areas...",
      relevance: 0.87,
      connections: [
        { label: "CoreCivic Contract", href: "#", source: "contracts" },
        { label: "Doe v. ICE", href: "#", source: "legal" },
        { label: "N368CA Flight Log", href: "#", source: "flights" },
      ],
    },
    {
      id: "result-sec-1",
      source: "sec",
      title: "GEO Group Inc - 10-Q Filing, Q3 2025",
      details: "CIK: 0000923796 | Filed Oct 30, 2025",
      excerpt:
        "Revenue from U.S. Immigration and Customs Enforcement contracts increased 22% year-over-year to $198M, driven by expanded detention facility capacity and new processing center operations. Management noted increased demand for secure transportation services...",
      relevance: 0.84,
      connections: [
        { label: "GEO Group Contract", href: "#", source: "contracts" },
        { label: "Ramirez v. GEO Group", href: "#", source: "legal" },
      ],
    },
    {
      id: "result-legal-2",
      source: "legal",
      title: "Garcia et al. v. DHS, Case No. 1:25-cv-00091",
      details: "S.D. California | Filed Jan 22, 2025 | Deportation (NOS 462)",
      excerpt:
        "Class action challenging conditions of confinement at Otay Mesa Detention Center, alleging systemic failures in medical care, unsanitary facility conditions, and violations of detainee rights under the Fifth Amendment due process clause...",
      relevance: 0.81,
      connections: [
        { label: "CoreCivic SEC Filing", href: "#", source: "sec" },
        { label: "Contract HSCEMD-25-C-00142", href: "#", source: "contracts" },
        { label: "ICE Detention Scrutiny", href: "#", source: "news" },
      ],
    },
  ];
}

export default function SearchPage() {
  const [query, setQuery] = useState("detention facility conditions");
  const [activeFilters, setActiveFilters] = useState<Set<FilterType>>(
    new Set<FilterType>(["all"])
  );
  const [results, setResults] = useState<SearchResult[]>([]);

  useEffect(() => {
    if (query.trim()) {
      setResults(buildMockResults());
    } else {
      setResults([]);
    }
  }, [query]);

  function toggleFilter(filter: FilterType) {
    setActiveFilters((prev) => {
      const next = new Set<FilterType>(prev);

      if (filter === "all") {
        return new Set<FilterType>(["all"]);
      }

      next.delete("all");

      if (next.has(filter)) {
        next.delete(filter);
      } else {
        next.add(filter);
      }

      if (next.size === 0) {
        return new Set<FilterType>(["all"]);
      }

      return next;
    });
  }

  const filteredResults = results.filter((r) => {
    if (activeFilters.has("all")) return true;
    return activeFilters.has(r.source);
  });

  return (
    <div
      className="min-h-screen"
      style={{ background: "var(--background)" }}
    >
      {/* Search Hero */}
      <section className="border-b border-[var(--border)] py-16">
        <div className="mx-auto max-w-2xl px-6">
          <div className="relative">
            <Search
              className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2"
              style={{ color: "var(--text-muted)" }}
            />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search across contracts, filings, cases, and news..."
              className="w-full rounded-xl py-4 pl-12 pr-12 text-lg outline-none transition-colors"
              style={{
                background: "var(--surface)",
                border: "1px solid var(--border)",
                color: "var(--foreground)",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "var(--primary)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "var(--border)";
              }}
            />
            {query && (
              <button
                onClick={() => setQuery("")}
                className="absolute right-4 top-1/2 -translate-y-1/2 rounded-md p-1 transition-colors hover:bg-[var(--surface-hover)]"
                style={{ color: "var(--text-muted)" }}
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
          {query && (
            <p
              className="mt-3 text-center text-sm"
              style={{ color: "var(--text-muted)" }}
            >
              Searching for:{" "}
              <span style={{ color: "var(--foreground)", fontWeight: 500 }}>
                {query}
              </span>
            </p>
          )}
        </div>
      </section>

      {/* Filters & Results */}
      <div className="mx-auto max-w-4xl px-6 py-8">
        {/* Source Filter Chips */}
        <div className="flex flex-wrap items-center gap-2">
          {FILTER_CHIPS.map((chip) => {
            const isActive = activeFilters.has(chip.value);
            return (
              <button
                key={chip.value}
                onClick={() => toggleFilter(chip.value)}
                className="rounded-full px-4 py-1.5 text-sm font-medium transition-all"
                style={{
                  background: isActive
                    ? "color-mix(in srgb, var(--primary) 15%, transparent)"
                    : "var(--surface)",
                  color: isActive
                    ? "var(--primary)"
                    : "var(--text-secondary)",
                  border: isActive
                    ? "1px solid color-mix(in srgb, var(--primary) 30%, transparent)"
                    : "1px solid var(--border)",
                }}
              >
                {chip.label}
              </button>
            );
          })}
        </div>

        {/* Sort & Date */}
        <div
          className="mt-4 flex items-center gap-3"
          style={{ color: "var(--text-secondary)" }}
        >
          <button
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm transition-colors hover:bg-[var(--surface-hover)]"
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
            }}
          >
            <SlidersHorizontal className="h-3.5 w-3.5" />
            Sort: Relevance
          </button>
          <button
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm transition-colors hover:bg-[var(--surface-hover)]"
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
            }}
          >
            Date: Any time
          </button>
        </div>

        {/* Results */}
        <div className="mt-8">
          {!query.trim() ? (
            <div className="flex flex-col items-center justify-center py-24 text-center">
              <Search
                className="mb-4 h-12 w-12"
                style={{ color: "var(--text-muted)" }}
              />
              <h2
                className="text-xl font-semibold"
                style={{ color: "var(--foreground)" }}
              >
                Search across all sources
              </h2>
              <p
                className="mt-2 max-w-md text-sm"
                style={{ color: "var(--text-muted)" }}
              >
                Enter a query to search across federal contracts, SEC filings,
                court cases, GDELT news events, and flight records.
              </p>
            </div>
          ) : (
            <>
              {/* Results header */}
              <div className="mb-6 flex items-baseline justify-between">
                <h2
                  className="text-lg font-semibold"
                  style={{ color: "var(--foreground)" }}
                >
                  Results for &ldquo;{query}&rdquo;
                </h2>
                <span
                  className="text-sm"
                  style={{ color: "var(--text-muted)" }}
                >
                  1,247 results
                </span>
              </div>

              {/* Result cards */}
              <div className="flex flex-col gap-4">
                {filteredResults.map((result) => {
                  const stripeColor = SOURCE_COLORS[result.source];

                  return (
                    <article
                      key={result.id}
                      className="group relative overflow-hidden rounded-xl transition-all hover:shadow-lg"
                      style={{
                        background: "var(--surface)",
                        border: "1px solid var(--border)",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = `${stripeColor}50`;
                        e.currentTarget.style.background = "var(--surface-hover)";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = "var(--border)";
                        e.currentTarget.style.background = "var(--surface)";
                      }}
                    >
                      {/* Left colored stripe */}
                      <div
                        className="absolute left-0 top-0 h-full w-1"
                        style={{ background: stripeColor }}
                      />

                      <div className="p-5 pl-6">
                        {/* Top row: badge + relevance */}
                        <div className="flex items-start justify-between">
                          <div className="flex flex-col gap-2">
                            <SourceBadge source={result.source} />
                            <h3
                              className="text-base font-semibold leading-snug"
                              style={{ color: "var(--foreground)" }}
                            >
                              {result.title}
                            </h3>
                          </div>

                          {/* Relevance score badge */}
                          <span
                            className="ml-4 shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold tabular-nums"
                            style={{
                              background: `${stripeColor}15`,
                              color: stripeColor,
                            }}
                          >
                            {result.relevance.toFixed(2)}
                          </span>
                        </div>

                        {/* Details */}
                        <p
                          className="mt-1 text-sm"
                          style={{ color: "var(--text-secondary)" }}
                        >
                          {result.details}
                        </p>

                        {/* Excerpt with highlighted terms */}
                        <p
                          className="mt-3 text-sm leading-relaxed"
                          style={{ color: "var(--text-muted)" }}
                        >
                          {highlightTerms(result.excerpt, query)}
                        </p>

                        {/* Connected chips */}
                        {result.connections.length > 0 && (
                          <div className="mt-4">
                            <ConnectedChips connections={result.connections} />
                          </div>
                        )}
                      </div>
                    </article>
                  );
                })}
              </div>

              {/* No results for filter */}
              {filteredResults.length === 0 && (
                <div className="flex flex-col items-center py-16 text-center">
                  <p
                    className="text-sm"
                    style={{ color: "var(--text-muted)" }}
                  >
                    No results match the selected filters. Try selecting
                    different source types.
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
