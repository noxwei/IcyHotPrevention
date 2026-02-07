"use client";

import Link from "next/link";
import {
  DollarSign,
  Building2,
  Scale,
  Newspaper,
  Plane,
  ArrowRight,
  Search,
} from "lucide-react";
import StatCard from "@/components/stat-card";
import FlightMapPlaceholder from "@/components/flight-map-placeholder";
import {
  TRACKED_AIRCRAFT,
  MOCK_CONTRACTS,
  MOCK_LEGAL_CASES,
  MOCK_NEWS_EVENTS,
  formatCurrency,
  timeAgo,
} from "@/lib/constants";

// Enrich airborne aircraft with mock positional data
const aircraftWithPositions = TRACKED_AIRCRAFT.map((ac) => {
  if (ac.status === "airborne") {
    const positions: Record<string, { lat: number; lng: number; altitude: number; heading: number }> = {
      N368CA: { lat: 29.5, lng: -98.3, altitude: 35000, heading: 225 },
      N406SW: { lat: 33.9, lng: -84.2, altitude: 28000, heading: 180 },
      N802WA: { lat: 25.8, lng: -80.3, altitude: 22000, heading: 160 },
    };
    const pos = positions[ac.registration] ?? {
      lat: 32.0,
      lng: -96.0,
      altitude: 30000,
      heading: 200,
    };
    return { ...ac, ...pos };
  }
  return { ...ac };
});

export default function Home() {
  const topContracts = MOCK_CONTRACTS.slice(0, 3);
  const topCases = MOCK_LEGAL_CASES.slice(0, 3);

  return (
    <div className="min-h-screen">
      {/* ===== Hero Section ===== */}
      <section className="relative overflow-hidden py-20 md:py-28">
        {/* Subtle radial gradient backdrop */}
        <div
          className="pointer-events-none absolute inset-0 opacity-30"
          style={{
            background:
              "radial-gradient(ellipse 60% 50% at 50% 0%, var(--primary), transparent)",
          }}
        />

        <div className="relative mx-auto max-w-7xl px-6 text-center">
          {/* Live badge */}
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--surface)] px-4 py-1.5 text-xs font-medium text-[var(--text-secondary)]">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[var(--success)] opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-[var(--success)]" />
            </span>
            Live Dashboard &mdash; 5 Data Sources
          </div>

          <h1 className="text-3xl font-bold tracking-tight md:text-5xl">
            IMMIGRATION ENFORCEMENT
            <br />
            <span className="text-[var(--primary)]">TRANSPARENCY</span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-base text-[var(--text-secondary)] md:text-lg">
            Tracking $2.54B in federal contracts, 7 aircraft, and 12,847 legal
            proceedings across 5 public data sources.
          </p>

          {/* Search bar CTA */}
          <Link
            href="/search"
            className="mx-auto mt-10 flex max-w-xl items-center gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] px-5 py-3.5 text-left transition-all hover:border-[var(--primary)]/50 hover:bg-[var(--surface-hover)]"
          >
            <Search className="h-5 w-5 shrink-0 text-[var(--text-muted)]" />
            <span className="flex-1 text-sm text-[var(--text-muted)]">
              Search contracts, companies, court cases, news...
            </span>
            <kbd className="hidden rounded border border-[var(--border)] px-2 py-0.5 font-mono text-[10px] text-[var(--text-muted)] sm:inline-block">
              /
            </kbd>
          </Link>
        </div>
      </section>

      {/* ===== Flight Map Section ===== */}
      <section className="mx-auto max-w-7xl px-6 py-16">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <Plane className="h-5 w-5 text-[var(--accent)]" />
              ICE Charter Flight Tracker
            </h2>
            <p className="mt-1 text-sm text-[var(--text-muted)]">
              Real-time positions of tracked deportation charter aircraft
            </p>
          </div>
          <Link
            href="/explore/flights"
            className="flex items-center gap-1.5 text-sm text-[var(--primary)] transition-colors hover:text-[var(--primary)]/80"
          >
            All flights
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <FlightMapPlaceholder aircraft={aircraftWithPositions} />
      </section>

      {/* ===== Stat Cards Section ===== */}
      <section className="mx-auto max-w-7xl px-6 py-16">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Contracts"
            value="$2.54B"
            subtitle="+12% YoY"
            icon={DollarSign}
            trend="+12%"
            trendUp={true}
          />
          <StatCard
            title="Tracked Companies"
            value="8"
            subtitle="3 flagged"
            icon={Building2}
            trend="3 flagged"
            trendUp={false}
          />
          <StatCard
            title="Court Cases"
            value="12,847"
            subtitle="+340/mo"
            icon={Scale}
            trend="+340/mo"
            trendUp={true}
          />
          <StatCard
            title="News Events"
            value="1.2M"
            subtitle="Updated 15m ago"
            icon={Newspaper}
          />
        </div>
      </section>

      {/* ===== Recent Activity Section ===== */}
      <section className="mx-auto max-w-7xl px-6 py-16">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Latest Contract Awards */}
          <div>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="flex items-center gap-2 text-lg font-semibold">
                <DollarSign className="h-5 w-5 text-[var(--accent)]" />
                Latest Contract Awards
              </h2>
            </div>

            <div className="flex flex-col gap-3">
              {topContracts.map((contract) => (
                <div
                  key={contract.id}
                  className="group rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 transition-colors hover:bg-[var(--surface-hover)]"
                >
                  <div className="flex items-start gap-3">
                    {/* Amber dot indicator */}
                    <span className="mt-1.5 inline-flex h-2.5 w-2.5 shrink-0 rounded-full bg-[var(--accent)]" />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-semibold text-[var(--foreground)]">
                          {contract.contractor}
                        </span>
                        <span className="shrink-0 font-mono text-sm font-bold text-[var(--accent)]">
                          {formatCurrency(contract.amount)}
                        </span>
                      </div>
                      <p className="mt-1 line-clamp-2 text-xs text-[var(--text-muted)]">
                        {contract.description}
                      </p>
                      <div className="mt-2 flex items-center gap-2 text-xs text-[var(--text-muted)]">
                        <span className="font-mono">{contract.id}</span>
                        <span>&middot;</span>
                        <span>{contract.agency}</span>
                        <span>&middot;</span>
                        <span>FY{contract.fy}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <Link
              href="/explore/contracts"
              className="mt-4 flex items-center gap-1.5 text-sm text-[var(--primary)] transition-colors hover:text-[var(--primary)]/80"
            >
              View all contracts
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {/* Latest Legal Filings */}
          <div>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="flex items-center gap-2 text-lg font-semibold">
                <Scale className="h-5 w-5 text-[var(--primary)]" />
                Latest Legal Filings
              </h2>
            </div>

            <div className="flex flex-col gap-3">
              {topCases.map((legalCase) => (
                <div
                  key={legalCase.id}
                  className="group rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 transition-colors hover:bg-[var(--surface-hover)]"
                >
                  <div className="flex items-start gap-3">
                    {/* Blue dot indicator */}
                    <span className="mt-1.5 inline-flex h-2.5 w-2.5 shrink-0 rounded-full bg-[var(--primary)]" />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-semibold text-[var(--foreground)]">
                          {legalCase.title}
                        </span>
                        <span className="shrink-0 text-xs text-[var(--text-muted)]">
                          {timeAgo(legalCase.filed)}
                        </span>
                      </div>
                      <div className="mt-1 flex items-center gap-2 text-xs text-[var(--text-secondary)]">
                        <span>{legalCase.court}</span>
                        <span>&middot;</span>
                        <span className="font-mono">{legalCase.id}</span>
                      </div>
                      <p className="mt-1.5 line-clamp-2 text-xs text-[var(--text-muted)]">
                        {legalCase.excerpt}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <Link
              href="/explore/legal"
              className="mt-4 flex items-center gap-1.5 text-sm text-[var(--primary)] transition-colors hover:text-[var(--primary)]/80"
            >
              View all cases
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* ===== News Ticker Section ===== */}
      <section className="mx-auto max-w-7xl px-6 py-16">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <Newspaper className="h-5 w-5 text-[var(--success)]" />
            News Events
          </h2>
          <Link
            href="/explore/news"
            className="flex items-center gap-1.5 text-sm text-[var(--primary)] transition-colors hover:text-[var(--primary)]/80"
          >
            All events
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="flex gap-4 overflow-x-auto pb-4">
          {MOCK_NEWS_EVENTS.map((event) => {
            const isNegative = event.goldstein < 0;

            return (
              <div
                key={event.id}
                className="group flex w-[320px] shrink-0 flex-col justify-between rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 transition-colors hover:bg-[var(--surface-hover)]"
              >
                <div>
                  <div className="mb-3 flex items-center justify-between text-xs">
                    <span className="rounded-full bg-[var(--surface-hover)] px-2.5 py-0.5 font-medium text-[var(--text-secondary)]">
                      {event.source}
                    </span>
                    <span className="text-[var(--text-muted)]">
                      {timeAgo(event.date)}
                    </span>
                  </div>

                  <h3 className="text-sm font-medium leading-snug text-[var(--foreground)] group-hover:text-white">
                    {event.title}
                  </h3>
                </div>

                <div className="mt-4 flex items-center justify-between border-t border-[var(--border)] pt-3 text-xs">
                  <div className="flex items-center gap-3">
                    <span className="text-[var(--text-muted)]">
                      {event.mentions} mentions
                    </span>
                  </div>
                  <span
                    className={`font-mono font-bold ${
                      isNegative
                        ? "text-[var(--danger)]"
                        : "text-[var(--success)]"
                    }`}
                  >
                    {event.goldstein > 0 ? "+" : ""}
                    {event.goldstein.toFixed(1)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        <p className="mt-2 text-xs text-[var(--text-muted)]">
          Goldstein Scale: measures theoretical impact of events on stability
          (range -10 to +10). Negative values indicate increased conflict.
        </p>
      </section>
    </div>
  );
}
