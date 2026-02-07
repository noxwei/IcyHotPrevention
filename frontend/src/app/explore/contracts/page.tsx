"use client";

import {
  TOP_CONTRACTORS,
  SPENDING_BY_YEAR,
  MOCK_CONTRACTS,
  formatCurrency,
} from "@/lib/constants";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  CartesianGrid,
} from "recharts";
import {
  Download,
  Filter,
  ChevronDown,
  ExternalLink,
  DollarSign,
  TrendingUp,
  Building2,
} from "lucide-react";
import SourceBadge from "@/components/source-badge";
import ConnectedChips from "@/components/connected-chips";

/* ------------------------------------------------------------------ */
/*  Mock connection data for certain contracts                        */
/* ------------------------------------------------------------------ */
const CONTRACT_CONNECTIONS: Record<
  string,
  { label: string; href: string; source: "contracts" | "sec" | "legal" | "news" | "flights" }[]
> = {
  "HSCEMD-25-C-00142": [
    { label: "SEC Filing - CoreCivic 10-K", href: "/explore/corporate?q=CoreCivic", source: "sec" },
    { label: "Garcia et al. v. DHS", href: "/explore/legal?id=1:25-cv-00091", source: "legal" },
  ],
  "HSCEMD-25-C-00098": [
    { label: "SEC Filing - Palantir S-1", href: "/explore/corporate?q=Palantir", source: "sec" },
  ],
  "HSCEMD-25-C-00176": [
    { label: "Ramirez v. GEO Group", href: "/explore/legal?id=3:24-cv-08901", source: "legal" },
  ],
  "HSCEMD-24-C-00312": [
    { label: "SEC Filing - Leidos 10-Q", href: "/explore/corporate?q=Leidos", source: "sec" },
  ],
};

/* ------------------------------------------------------------------ */
/*  Recharts tooltip shared style                                     */
/* ------------------------------------------------------------------ */
const TOOLTIP_STYLE = {
  backgroundColor: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: "8px",
  color: "var(--foreground)",
};

/* ------------------------------------------------------------------ */
/*  Summary stats derived from data                                   */
/* ------------------------------------------------------------------ */
const totalObligated = TOP_CONTRACTORS.reduce((sum, c) => sum + c.amount, 0);
const latestYear = SPENDING_BY_YEAR[SPENDING_BY_YEAR.length - 1];
const previousYear = SPENDING_BY_YEAR[SPENDING_BY_YEAR.length - 2];
const yoyGrowth = (
  ((latestYear.total - previousYear.total) / previousYear.total) *
  100
).toFixed(1);

/* ------------------------------------------------------------------ */
/*  Page                                                              */
/* ------------------------------------------------------------------ */
export default function ContractsExplorerPage() {
  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      {/* ---------------------------------------------------------- */}
      {/*  1. Page Header                                            */}
      {/* ---------------------------------------------------------- */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">
              Contracts
            </h1>
            <SourceBadge source="contracts" />
          </div>
          <p className="mt-2 max-w-xl text-sm text-[var(--text-secondary)]">
            Federal spending on immigration enforcement via USASpending.gov
          </p>
        </div>

        <button
          className="inline-flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2 text-sm font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-hover)]"
        >
          <Download className="h-4 w-4" />
          Export
        </button>
      </div>

      {/* ---------------------------------------------------------- */}
      {/*  Summary stat pills                                        */}
      {/* ---------------------------------------------------------- */}
      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="flex items-center gap-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--accent)]/15">
            <DollarSign className="h-5 w-5 text-[var(--accent)]" />
          </div>
          <div>
            <div className="text-2xl font-bold tracking-tight text-[var(--foreground)]">
              {formatCurrency(totalObligated)}
            </div>
            <div className="text-xs text-[var(--text-muted)]">Top-7 Contractor Obligations</div>
          </div>
        </div>

        <div className="flex items-center gap-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--primary)]/15">
            <TrendingUp className="h-5 w-5 text-[var(--primary)]" />
          </div>
          <div>
            <div className="text-2xl font-bold tracking-tight text-[var(--foreground)]">
              +{yoyGrowth}%
            </div>
            <div className="text-xs text-[var(--text-muted)]">YoY Spending Growth</div>
          </div>
        </div>

        <div className="flex items-center gap-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--success)]/15">
            <Building2 className="h-5 w-5 text-[var(--success)]" />
          </div>
          <div>
            <div className="text-2xl font-bold tracking-tight text-[var(--foreground)]">
              {TOP_CONTRACTORS.length}
            </div>
            <div className="text-xs text-[var(--text-muted)]">Tracked Contractors</div>
          </div>
        </div>
      </div>

      {/* ---------------------------------------------------------- */}
      {/*  2. Filter Bar                                             */}
      {/* ---------------------------------------------------------- */}
      <div className="mt-8 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--text-secondary)]">
          <Filter className="h-3.5 w-3.5 text-[var(--text-muted)]" />
          Filters
        </div>

        {["Fiscal Year", "Agency", "Contractor"].map((label) => (
          <button
            key={label}
            className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-hover)]"
          >
            {label}
            <ChevronDown className="h-3.5 w-3.5 text-[var(--text-muted)]" />
          </button>
        ))}

        <input
          type="text"
          placeholder="Min $"
          readOnly
          className="w-24 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--text-secondary)] placeholder:text-[var(--text-muted)] focus:outline-none"
        />
        <input
          type="text"
          placeholder="Max $"
          readOnly
          className="w-24 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--text-secondary)] placeholder:text-[var(--text-muted)] focus:outline-none"
        />
      </div>

      {/* ---------------------------------------------------------- */}
      {/*  3. Top Contractors Bar Chart                              */}
      {/* ---------------------------------------------------------- */}
      <section className="mt-8 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6">
        <h2 className="mb-6 text-lg font-semibold text-[var(--foreground)]">
          Top Contractors by Obligation
        </h2>

        <ResponsiveContainer width="100%" height={360}>
          <BarChart
            data={[...TOP_CONTRACTORS]}
            layout="vertical"
            margin={{ top: 0, right: 40, bottom: 0, left: 0 }}
          >
            <XAxis
              type="number"
              tickFormatter={(v: number) => formatCurrency(v)}
              tick={{ fill: "var(--text-muted)", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={160}
              tick={{ fill: "var(--text-secondary)", fontSize: 13 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={TOOLTIP_STYLE}
              formatter={(value: number | undefined) => [formatCurrency(value ?? 0), "Obligated"]}
              cursor={{ fill: "var(--surface-hover)" }}
            />
            <Bar
              dataKey="amount"
              fill="var(--accent)"
              radius={[0, 6, 6, 0]}
              barSize={28}
            />
          </BarChart>
        </ResponsiveContainer>
      </section>

      {/* ---------------------------------------------------------- */}
      {/*  4. Spending Over Time Area Chart                          */}
      {/* ---------------------------------------------------------- */}
      <section className="mt-8 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6">
        <h2 className="mb-6 text-lg font-semibold text-[var(--foreground)]">
          Spending Over Time
        </h2>

        <ResponsiveContainer width="100%" height={340}>
          <AreaChart
            data={[...SPENDING_BY_YEAR]}
            margin={{ top: 10, right: 30, bottom: 0, left: 10 }}
          >
            <defs>
              <linearGradient id="colorLeidos" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#4F8EF7" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#4F8EF7" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorGenDyn" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#F59E0B" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorPalantir" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorOther" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6B7280" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#6B7280" stopOpacity={0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" strokeOpacity={0.5} />

            <XAxis
              dataKey="year"
              tick={{ fill: "var(--text-muted)", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "var(--text-muted)", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              label={{
                value: "$M",
                position: "insideTopLeft",
                offset: -5,
                style: { fill: "var(--text-muted)", fontSize: 12 },
              }}
            />
            <Tooltip
              contentStyle={TOOLTIP_STYLE}
              formatter={(value: number | undefined, name: string | undefined) => {
                const labels: Record<string, string> = {
                  leidos: "Leidos",
                  genDyn: "General Dynamics",
                  palantir: "Palantir",
                  other: "Other",
                };
                const key = name ?? "";
                return [`$${value ?? 0}M`, labels[key] ?? key];
              }}
            />

            <Area
              type="monotone"
              dataKey="other"
              stackId="1"
              stroke="#6B7280"
              fill="url(#colorOther)"
              fillOpacity={1}
            />
            <Area
              type="monotone"
              dataKey="palantir"
              stackId="1"
              stroke="#10B981"
              fill="url(#colorPalantir)"
              fillOpacity={1}
            />
            <Area
              type="monotone"
              dataKey="genDyn"
              stackId="1"
              stroke="#F59E0B"
              fill="url(#colorGenDyn)"
              fillOpacity={1}
            />
            <Area
              type="monotone"
              dataKey="leidos"
              stackId="1"
              stroke="#4F8EF7"
              fill="url(#colorLeidos)"
              fillOpacity={1}
            />
          </AreaChart>
        </ResponsiveContainer>

        {/* Legend */}
        <div className="mt-4 flex flex-wrap items-center justify-center gap-6 text-xs text-[var(--text-secondary)]">
          {[
            { label: "Leidos", color: "#4F8EF7" },
            { label: "General Dynamics", color: "#F59E0B" },
            { label: "Palantir", color: "#10B981" },
            { label: "Other", color: "#6B7280" },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-2">
              <span
                className="inline-block h-3 w-3 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              {item.label}
            </div>
          ))}
        </div>
      </section>

      {/* ---------------------------------------------------------- */}
      {/*  5. Contract Table                                         */}
      {/* ---------------------------------------------------------- */}
      <section className="mt-8 rounded-xl border border-[var(--border)] bg-[var(--surface)]">
        <div className="flex items-center justify-between border-b border-[var(--border)] px-6 py-4">
          <h2 className="text-lg font-semibold text-[var(--foreground)]">
            Recent Awards
          </h2>
          <span className="text-xs text-[var(--text-muted)]">
            {MOCK_CONTRACTS.length} contracts
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] text-left text-xs font-medium uppercase tracking-wider text-[var(--text-muted)]">
                <th className="px-6 py-3">Award ID</th>
                <th className="px-6 py-3">Contractor</th>
                <th className="px-6 py-3 text-right">Amount</th>
                <th className="px-6 py-3">Agency</th>
                <th className="px-6 py-3">FY</th>
                <th className="px-6 py-3">Description</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_CONTRACTS.map((contract) => {
                const connections = CONTRACT_CONNECTIONS[contract.id] ?? [];

                return (
                  <tr
                    key={contract.id}
                    className="border-b border-[var(--border)] transition-colors hover:bg-[var(--surface-hover)]"
                  >
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[var(--primary)]">
                          {contract.id}
                        </span>
                        <ExternalLink className="h-3 w-3 text-[var(--text-muted)]" />
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 font-medium text-[var(--foreground)]">
                      {contract.contractor}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right font-mono text-[var(--accent)]">
                      {formatCurrency(contract.amount)}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-[var(--text-secondary)]">
                      {contract.agency}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-[var(--text-secondary)]">
                      {contract.fy}
                    </td>
                    <td className="max-w-xs px-6 py-4">
                      <p className="truncate text-[var(--text-secondary)]">
                        {contract.description}
                      </p>
                      {connections.length > 0 && (
                        <div className="mt-2">
                          <ConnectedChips connections={connections} />
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
