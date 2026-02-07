"use client";

import Link from "next/link";
import {
  Building2,
  TrendingUp,
  AlertTriangle,
  ExternalLink,
  ArrowRight,
  DollarSign,
  BarChart3,
} from "lucide-react";

interface Company {
  name: string;
  cik: string;
  sector: string;
  revenue: string;
  netIncome?: string;
  anomaly?: { label: string; detail: string };
  sparklineStyle?: string;
}

const COMPANIES: Company[] = [
  {
    name: "GEO Group",
    cik: "0000923796",
    sector: "Private prisons",
    revenue: "$2.4B",
    netIncome: "$174M",
    anomaly: { label: "ANOMALY", detail: "+540% QoQ net income" },
  },
  {
    name: "CoreCivic",
    cik: "0001070985",
    sector: "Private prisons",
    revenue: "$1.9B",
    netIncome: "$42M",
  },
  {
    name: "Palantir",
    cik: "0001321655",
    sector: "Data/surveillance",
    revenue: "$2.2B",
    netIncome: "$210M",
  },
  {
    name: "General Dynamics",
    cik: "0000040533",
    sector: "IT services",
    revenue: "$42.3B",
  },
  {
    name: "Leidos",
    cik: "0001336920",
    sector: "Border tech",
    revenue: "$15.4B",
  },
  {
    name: "Northrop Grumman",
    cik: "0000072945",
    sector: "Surveillance",
    revenue: "$36.8B",
  },
  {
    name: "L3Harris",
    cik: "0000202058",
    sector: "Detection systems",
    revenue: "$19.4B",
  },
  {
    name: "Raytheon/RTX",
    cik: "0000082267",
    sector: "Border security",
    revenue: "$68.9B",
  },
];

export default function CorporatePage() {
  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      {/* Page Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--primary)]/15">
            <Building2 className="h-5 w-5 text-[var(--primary)]" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">
              Corporate Filings
            </h1>
            <p className="text-sm text-[var(--text-secondary)]">
              SEC EDGAR financial data from immigration enforcement contractors
            </p>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
          <div className="text-xs text-[var(--text-muted)] mb-1">Companies Tracked</div>
          <div className="text-2xl font-bold text-[var(--foreground)]">8</div>
        </div>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
          <div className="text-xs text-[var(--text-muted)] mb-1">Combined Revenue</div>
          <div className="text-2xl font-bold text-[var(--foreground)]">$189.9B</div>
        </div>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
          <div className="text-xs text-[var(--text-muted)] mb-1">Filings Indexed</div>
          <div className="text-2xl font-bold text-[var(--foreground)]">2,841</div>
        </div>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
          <div className="text-xs text-[var(--text-muted)] mb-1">Active Anomalies</div>
          <div className="flex items-center gap-2">
            <div className="text-2xl font-bold text-[var(--accent)]">1</div>
            <AlertTriangle className="h-4 w-4 text-[var(--accent)]" />
          </div>
        </div>
      </div>

      {/* Company Cards Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {COMPANIES.map((company) => {
          const hasAnomaly = !!company.anomaly;

          return (
            <div
              key={company.cik}
              className="rounded-xl border bg-[var(--surface)] p-6 transition-colors hover:bg-[var(--surface-hover)]"
              style={{
                borderColor: hasAnomaly ? "#F59E0B" : "var(--border)",
                borderWidth: hasAnomaly ? "2px" : "1px",
              }}
            >
              {/* Anomaly Alert */}
              {hasAnomaly && company.anomaly && (
                <div className="mb-4 flex items-start gap-3 rounded-lg border border-[var(--accent)]/30 bg-[var(--accent)]/10 px-4 py-3">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--accent)]" />
                  <div>
                    <span className="inline-flex items-center rounded-full bg-[var(--accent)]/20 px-2 py-0.5 text-[10px] font-bold tracking-wider text-[var(--accent)]">
                      {company.anomaly.label}
                    </span>
                    <p className="mt-1 text-xs text-[var(--accent)]">
                      {company.anomaly.detail}
                    </p>
                  </div>
                </div>
              )}

              {/* Company Header */}
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-xl font-semibold text-[var(--foreground)]">
                    {company.name}
                  </h2>
                  <p className="mt-1 font-mono text-xs text-[var(--text-muted)]">
                    CIK: {company.cik}
                  </p>
                </div>
                <span className="inline-flex items-center rounded-full border border-[var(--border)] bg-[var(--surface-hover)] px-2.5 py-1 text-xs font-medium text-[var(--text-secondary)]">
                  {company.sector}
                </span>
              </div>

              {/* Financial Metrics */}
              <div className="mb-4 flex flex-wrap gap-4">
                <div className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-[var(--text-muted)]" />
                  <div>
                    <div className="text-xs text-[var(--text-muted)]">Revenue</div>
                    <div className="text-sm font-semibold text-[var(--foreground)]">
                      {company.revenue}
                    </div>
                  </div>
                </div>
                {company.netIncome && (
                  <div className="flex items-center gap-2">
                    <BarChart3 className="h-4 w-4 text-[var(--text-muted)]" />
                    <div>
                      <div className="text-xs text-[var(--text-muted)]">Net Income</div>
                      <div className="flex items-center gap-1.5 text-sm font-semibold text-[var(--foreground)]">
                        {company.netIncome}
                        {hasAnomaly && (
                          <TrendingUp className="h-3.5 w-3.5 text-[var(--accent)]" />
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Sparkline Placeholder */}
              <div className="mb-4">
                <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] mb-2">
                  12-month revenue trend
                </div>
                <div
                  className="h-10 w-full rounded-md"
                  style={{
                    background: `linear-gradient(90deg, ${hasAnomaly ? "var(--accent)" : "var(--primary)"}15, ${hasAnomaly ? "var(--accent)" : "var(--primary)"}05)`,
                    borderBottom: `2px solid ${hasAnomaly ? "var(--accent)" : "var(--primary)"}`,
                    borderBottomStyle: "dotted",
                  }}
                />
              </div>

              {/* View Link */}
              <Link
                href={`https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=${company.cik}&type=10-K&dateb=&owner=include&count=40`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-sm font-medium text-[var(--primary)] transition-colors hover:text-[var(--primary)]/80"
              >
                View SEC Filings
                <ArrowRight className="h-4 w-4" />
                <ExternalLink className="h-3 w-3 opacity-50" />
              </Link>
            </div>
          );
        })}
      </div>
    </div>
  );
}
