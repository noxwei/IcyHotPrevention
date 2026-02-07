"use client";

import { useState } from "react";
import {
  Scale,
  Filter,
  ChevronDown,
  FileText,
  Calendar,
  Hash,
} from "lucide-react";
import { MOCK_LEGAL_CASES, timeAgo } from "@/lib/constants";
import SourceBadge from "@/components/source-badge";
import ConnectedChips from "@/components/connected-chips";

const MOCK_CONNECTIONS: Record<string, { label: string; href: string; source: "contracts" | "sec" | "legal" | "news" | "flights" }[]> = {
  "4:24-cv-01234": [
    { label: "CoreCivic Contract $45.2M", href: "/explore/contracts", source: "contracts" },
    { label: "CoreCivic 10-K Filing", href: "/explore/corporate", source: "sec" },
  ],
  "2:24-cv-05678": [
    { label: "CBP Surveillance Spend", href: "/explore/contracts", source: "contracts" },
  ],
  "1:25-cv-00091": [
    { label: "DHS Detention Budget", href: "/explore/contracts", source: "contracts" },
    { label: "Conditions Report - Reuters", href: "/explore/news", source: "news" },
  ],
  "3:24-cv-08901": [
    { label: "GEO Group 10-Q", href: "/explore/corporate", source: "sec" },
  ],
};

export default function LegalPage() {
  const [courtFilter, setCourtFilter] = useState("all");
  const [nosFilter, setNosFilter] = useState("all");
  const [dateFilter, setDateFilter] = useState("all");

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#8B5CF6]/15">
            <Scale className="h-5 w-5 text-[#8B5CF6]" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">
              Legal Cases
            </h1>
            <p className="text-sm text-[var(--text-secondary)]">
              Immigration-related court proceedings via CourtListener
            </p>
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <Filter className="h-4 w-4 text-[var(--text-muted)]" />

        {/* Court Filter */}
        <div className="relative">
          <select
            value={courtFilter}
            onChange={(e) => setCourtFilter(e.target.value)}
            className="appearance-none rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 pr-8 text-sm text-[var(--text-secondary)] transition-colors hover:border-[var(--primary)]/50 focus:border-[var(--primary)] focus:outline-none"
          >
            <option value="all">All Courts</option>
            <option value="sd-texas">S.D. Texas</option>
            <option value="d-arizona">D. Arizona</option>
            <option value="sd-california">S.D. California</option>
            <option value="wd-louisiana">W.D. Louisiana</option>
          </select>
          <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--text-muted)]" />
        </div>

        {/* Nature of Suit Filter */}
        <div className="relative">
          <select
            value={nosFilter}
            onChange={(e) => setNosFilter(e.target.value)}
            className="appearance-none rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 pr-8 text-sm text-[var(--text-secondary)] transition-colors hover:border-[var(--primary)]/50 focus:border-[var(--primary)] focus:outline-none"
          >
            <option value="all">All Nature of Suit</option>
            <option value="462">462 - Deportation</option>
            <option value="440">440 - Civil Rights</option>
            <option value="550">550 - Prisoner: Civil Rights</option>
          </select>
          <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--text-muted)]" />
        </div>

        {/* Date Range Filter */}
        <div className="relative">
          <select
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            className="appearance-none rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 pr-8 text-sm text-[var(--text-secondary)] transition-colors hover:border-[var(--primary)]/50 focus:border-[var(--primary)] focus:outline-none"
          >
            <option value="all">All Dates</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="1y">Last year</option>
          </select>
          <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--text-muted)]" />
        </div>
      </div>

      {/* Stats Row */}
      <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
          <div className="text-xs text-[var(--text-muted)] mb-1">Total Cases</div>
          <div className="text-2xl font-bold text-[var(--foreground)]">12,847</div>
        </div>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
          <div className="text-xs text-[var(--text-muted)] mb-1">462 - Deportation</div>
          <div className="text-2xl font-bold text-[#8B5CF6]">8,341</div>
        </div>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
          <div className="text-xs text-[var(--text-muted)] mb-1">440 - Civil Rights</div>
          <div className="text-2xl font-bold text-[var(--foreground)]">2,106</div>
        </div>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
          <div className="text-xs text-[var(--text-muted)] mb-1">Filed This Month</div>
          <div className="text-2xl font-bold text-[var(--success)]">340</div>
        </div>
      </div>

      {/* Case List */}
      <div className="space-y-4">
        {MOCK_LEGAL_CASES.map((legalCase) => (
          <div
            key={legalCase.id}
            className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 transition-colors hover:bg-[var(--surface-hover)]"
          >
            {/* Top row: case number, source badge, NOS badge */}
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
                <Hash className="h-3 w-3" />
                <span className="font-mono">{legalCase.id}</span>
              </div>
              <SourceBadge source="legal" />
              <span
                className="inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-semibold tracking-wide"
                style={{
                  backgroundColor: legalCase.nos.startsWith("462")
                    ? "#8B5CF615"
                    : "#F59E0B15",
                  color: legalCase.nos.startsWith("462")
                    ? "#8B5CF6"
                    : "#F59E0B",
                }}
              >
                {legalCase.nos}
              </span>
            </div>

            {/* Title */}
            <h3 className="text-lg font-semibold text-[var(--foreground)] mb-2">
              {legalCase.title}
            </h3>

            {/* Court and Date */}
            <div className="flex flex-wrap items-center gap-4 mb-3 text-sm text-[var(--text-secondary)]">
              <div className="flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-[var(--text-muted)]" />
                {legalCase.court}
              </div>
              <div className="flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5 text-[var(--text-muted)]" />
                Filed {timeAgo(legalCase.filed)}
              </div>
            </div>

            {/* Excerpt */}
            <p className="text-sm leading-relaxed text-[var(--text-muted)] mb-4">
              {legalCase.excerpt}
            </p>

            {/* Connected Chips */}
            <ConnectedChips
              connections={MOCK_CONNECTIONS[legalCase.id] || []}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
