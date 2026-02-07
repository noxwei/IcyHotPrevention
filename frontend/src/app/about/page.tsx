"use client";

import { useState } from "react";
import {
  DollarSign,
  Building2,
  Scale,
  Newspaper,
  Plane,
  Search,
  Shield,
  Cpu,
  ChevronDown,
  ExternalLink,
  Mail,
  Github,
  BookOpen,
  Database,
  Zap,
  Lock,
  Users,
} from "lucide-react";

const DATA_SOURCES = [
  {
    icon: DollarSign,
    color: "#F59E0B",
    name: "USASpending.gov",
    description:
      "Federal contract and grant awards to immigration enforcement agencies (ICE, CBP, EOIR). Tracks spending by contractor, agency, fiscal year, and Treasury Account Symbol.",
    frequency: "Daily updates",
    rateLimit: "1,000 requests/hour",
    link: "https://api.usaspending.gov",
  },
  {
    icon: Building2,
    color: "#4F8EF7",
    name: "SEC EDGAR",
    description:
      "Corporate financial filings (10-K, 10-Q, 8-K) from publicly traded companies with immigration enforcement contracts. Monitors revenue, income, and anomalous financial changes.",
    frequency: "Real-time filings",
    rateLimit: "10 requests/second",
    link: "https://efts.sec.gov/LATEST/search-index",
  },
  {
    icon: Scale,
    color: "#8B5CF6",
    name: "CourtListener",
    description:
      "Immigration-related federal court cases including deportation proceedings (NOS 462), civil rights cases (NOS 440), and conditions-of-confinement litigation.",
    frequency: "Hourly court updates",
    rateLimit: "5,000 requests/day",
    link: "https://www.courtlistener.com/api/rest/v4/",
  },
  {
    icon: Newspaper,
    color: "#10B981",
    name: "GDELT Project",
    description:
      "Global news event monitoring with Goldstein conflict scale scoring, actor coding, and tone analysis. Covers immigration enforcement events from worldwide media sources.",
    frequency: "Every 15 minutes",
    rateLimit: "Unlimited (BigQuery)",
    link: "https://www.gdeltproject.org",
  },
  {
    icon: Plane,
    color: "#EF4444",
    name: "OpenSky Network",
    description:
      "Real-time ADS-B transponder data for known ICE charter aircraft. Tracks flight paths, departure/arrival airports, and operational patterns of deportation flights.",
    frequency: "5-second intervals",
    rateLimit: "400 requests/day (anonymous)",
    link: "https://opensky-network.org/apidoc/",
  },
];

const FAQ_ITEMS = [
  {
    question: "Where does the data come from?",
    answer:
      "All data is sourced exclusively from public federal databases and open APIs. We do not use any non-public, leaked, or classified information. USASpending.gov, SEC EDGAR, CourtListener, GDELT, and OpenSky Network are all freely accessible public data sources maintained by government agencies, nonprofits, or academic institutions.",
  },
  {
    question: "How accurate is the entity resolution?",
    answer:
      "Our entity resolution system uses a hybrid approach combining exact matching, fuzzy string matching (Levenshtein distance), and embedding-based semantic similarity. We achieve approximately 94% precision on contractor name matching. When multiple records map to the same entity, we surface the connection with a confidence score and allow users to verify the linkage.",
  },
  {
    question: "What are the budget controls?",
    answer:
      "IETY operates under a strict $50/month infrastructure budget. We use tiered rate limiting across all API calls, aggressive caching (24h for contracts, 1h for filings, 15min for news), and a token-aware cost controller that tracks spending across OpenAI embeddings, database queries, and API calls. If monthly costs approach the limit, the system automatically falls back to cached data.",
  },
  {
    question: "Is personal data collected or stored?",
    answer:
      "No. IETY does not collect, store, or process any personally identifiable information (PII) about individuals. Our data pipeline focuses exclusively on institutional actors: government agencies, corporations, court dockets (public record), and news events. We do not track individuals, and we actively filter out PII that may appear in source documents.",
  },
  {
    question: "How can I use this data in my own research?",
    answer:
      "IETY provides a public REST API that returns structured JSON for all indexed data. Researchers can query contracts, filings, cases, and events with filters for date, entity, amount, and more. We ask that you cite IETY as a secondary source and always reference the primary data source (USASpending, SEC, etc.) in any publication. Rate limits apply to prevent abuse.",
  },
];

export default function AboutPage() {
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      {/* Hero */}
      <section className="mb-16 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-[var(--foreground)] sm:text-5xl">
          About IETY
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-[var(--text-secondary)]">
          IETY (Immigration Enforcement Transparency) is an open-source
          intelligence tool that aggregates, cross-references, and visualizes
          public data about the U.S. immigration enforcement system. By
          connecting federal spending records, corporate filings, court
          proceedings, global news events, and real-time flight tracking, we
          aim to make the opaque machinery of enforcement legible to
          journalists, researchers, legal advocates, and the public.
        </p>
      </section>

      {/* Data Sources */}
      <section className="mb-16">
        <div className="flex items-center gap-3 mb-8">
          <Database className="h-6 w-6 text-[var(--primary)]" />
          <h2 className="text-2xl font-bold text-[var(--foreground)]">
            Data Sources
          </h2>
        </div>

        <div className="space-y-4">
          {DATA_SOURCES.map((source) => (
            <div
              key={source.name}
              className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 transition-colors hover:bg-[var(--surface-hover)]"
            >
              <div className="flex items-start gap-4">
                {/* Icon */}
                <div
                  className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl"
                  style={{ backgroundColor: `${source.color}15` }}
                >
                  <source.icon
                    className="h-5 w-5"
                    style={{ color: source.color }}
                  />
                </div>

                {/* Content */}
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-[var(--foreground)]">
                      {source.name}
                    </h3>
                    <a
                      href={source.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs font-medium text-[var(--primary)] hover:text-[var(--primary)]/80"
                    >
                      API Docs
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>

                  <p className="text-sm leading-relaxed text-[var(--text-secondary)] mb-3">
                    {source.description}
                  </p>

                  <div className="flex flex-wrap gap-4 text-xs text-[var(--text-muted)]">
                    <span className="inline-flex items-center gap-1.5">
                      <Zap className="h-3 w-3" style={{ color: source.color }} />
                      {source.frequency}
                    </span>
                    <span className="inline-flex items-center gap-1.5">
                      <Lock className="h-3 w-3" />
                      {source.rateLimit}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Methodology */}
      <section className="mb-16">
        <div className="flex items-center gap-3 mb-8">
          <Cpu className="h-6 w-6 text-[var(--primary)]" />
          <h2 className="text-2xl font-bold text-[var(--foreground)]">
            Methodology
          </h2>
        </div>

        <div className="space-y-6 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6">
          {/* Hybrid Search */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Search className="h-4 w-4 text-[var(--primary)]" />
              <h3 className="text-base font-semibold text-[var(--foreground)]">
                Hybrid Search Architecture
              </h3>
            </div>
            <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
              IETY uses a hybrid retrieval system that combines{" "}
              <strong className="text-[var(--foreground)]">70% vector similarity search</strong>{" "}
              (via OpenAI text-embedding-3-small) with{" "}
              <strong className="text-[var(--foreground)]">30% BM25 keyword matching</strong>.
              This approach ensures that both semantic meaning and exact terms
              (like contract IDs, CIK numbers, and case docket numbers) are
              properly weighted in search results. Documents are chunked into
              512-token segments with 50-token overlap to maintain context
              across boundaries.
            </p>
          </div>

          {/* Entity Resolution */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Users className="h-4 w-4 text-[var(--primary)]" />
              <h3 className="text-base font-semibold text-[var(--foreground)]">
                Entity Resolution
              </h3>
            </div>
            <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
              Cross-source entity linking connects the same organizations across
              different databases. For example, "GEO Group, Inc." in SEC filings
              is matched to "The GEO Group" in USASpending contracts and
              "GEO Group" in court records. We use a combination of normalized
              name matching, EIN/CIK/DUNS identifiers, and manual curation for
              the top 50 immigration enforcement entities.
            </p>
          </div>

          {/* Budget Controls */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="h-4 w-4 text-[var(--accent)]" />
              <h3 className="text-base font-semibold text-[var(--foreground)]">
                Budget Controls
              </h3>
            </div>
            <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
              The entire system operates within a{" "}
              <strong className="text-[var(--accent)]">$50/month budget</strong>.
              A centralized cost controller tracks API calls to OpenAI (embeddings),
              Qdrant Cloud (vector DB), and external data APIs. Tiered caching
              reduces redundant API calls: contracts are cached for 24 hours,
              SEC filings for 1 hour, and GDELT events for 15 minutes. When
              costs approach 80% of the monthly budget, the system automatically
              increases cache TTLs and reduces embedding batch sizes.
            </p>
          </div>

          {/* Privacy */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Shield className="h-4 w-4 text-[var(--success)]" />
              <h3 className="text-base font-semibold text-[var(--foreground)]">
                Privacy Principles
              </h3>
            </div>
            <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
              IETY is designed around institutional transparency, not individual
              surveillance. We track government agencies, corporations, and
              public court proceedings -- never individuals. PII detection
              runs on all ingested text, and any identified personal data is
              redacted before indexing. We do not use cookies, analytics
              trackers, or any third-party monitoring on this website.
            </p>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="mb-16">
        <div className="flex items-center gap-3 mb-8">
          <BookOpen className="h-6 w-6 text-[var(--primary)]" />
          <h2 className="text-2xl font-bold text-[var(--foreground)]">
            Frequently Asked Questions
          </h2>
        </div>

        <div className="space-y-3">
          {FAQ_ITEMS.map((item, index) => (
            <details
              key={index}
              className="group rounded-xl border border-[var(--border)] bg-[var(--surface)] transition-colors hover:bg-[var(--surface-hover)]"
              open={openFaq === index}
              onToggle={(e) => {
                if ((e.target as HTMLDetailsElement).open) {
                  setOpenFaq(index);
                } else if (openFaq === index) {
                  setOpenFaq(null);
                }
              }}
            >
              <summary className="flex cursor-pointer items-center justify-between px-6 py-4 text-sm font-semibold text-[var(--foreground)] list-none [&::-webkit-details-marker]:hidden">
                {item.question}
                <ChevronDown className="h-4 w-4 shrink-0 text-[var(--text-muted)] transition-transform group-open:rotate-180" />
              </summary>
              <div className="border-t border-[var(--border)] px-6 py-4">
                <p className="text-sm leading-relaxed text-[var(--text-secondary)]">
                  {item.answer}
                </p>
              </div>
            </details>
          ))}
        </div>
      </section>

      {/* Contact Footer */}
      <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-8 text-center">
        <h2 className="text-xl font-bold text-[var(--foreground)] mb-3">
          Contact
        </h2>
        <p className="text-sm text-[var(--text-secondary)] mb-6 max-w-lg mx-auto">
          Questions, feedback, or data correction requests? We welcome
          contributions from journalists, researchers, and legal advocates.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-4">
          <a
            href="mailto:contact@iety.org"
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface-hover)] px-4 py-2.5 text-sm font-medium text-[var(--text-secondary)] transition-colors hover:border-[var(--primary)] hover:text-[var(--primary)]"
          >
            <Mail className="h-4 w-4" />
            contact@iety.org
          </a>
          <a
            href="https://github.com/iety-project"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface-hover)] px-4 py-2.5 text-sm font-medium text-[var(--text-secondary)] transition-colors hover:border-[var(--primary)] hover:text-[var(--primary)]"
          >
            <Github className="h-4 w-4" />
            GitHub
          </a>
          <a
            href="/api"
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--primary)] bg-[var(--primary)]/10 px-4 py-2.5 text-sm font-medium text-[var(--primary)] transition-colors hover:bg-[var(--primary)]/20"
          >
            <BookOpen className="h-4 w-4" />
            API Documentation
          </a>
        </div>
      </section>
    </div>
  );
}
