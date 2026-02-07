"use client";

import {
  Newspaper,
  Radio,
  TrendingDown,
  TrendingUp,
  MessageSquare,
  Globe,
  Minus,
} from "lucide-react";
import { MOCK_NEWS_EVENTS } from "@/lib/constants";

interface NewsEvent {
  id: string;
  title: string;
  source: string;
  date: string;
  goldstein: number;
  mentions: number;
  actors: string[];
}

const EXTRA_EVENTS: NewsEvent[] = [
  {
    id: "evt-004",
    title: "Congressional hearing examines ICE budget allocation",
    source: "NPR",
    date: "2025-01-21",
    goldstein: -1.0,
    mentions: 34,
    actors: ["USAGOV", "LEG"],
  },
  {
    id: "evt-005",
    title: "Advocacy groups report increase in family separations",
    source: "The Guardian",
    date: "2025-01-19",
    goldstein: -5.2,
    mentions: 51,
    actors: ["NGO", "USAGOV"],
  },
  {
    id: "evt-006",
    title: "Border technology contract awarded to Leidos subsidiary",
    source: "Defense One",
    date: "2025-01-17",
    goldstein: 1.5,
    mentions: 12,
    actors: ["USAGOV", "MIL"],
  },
  {
    id: "evt-007",
    title: "International organizations condemn deportation flights",
    source: "Al Jazeera",
    date: "2025-01-14",
    goldstein: -6.0,
    mentions: 73,
    actors: ["IGO", "USAGOV"],
  },
  {
    id: "evt-008",
    title: "State governors push back on federal immigration raids",
    source: "Politico",
    date: "2025-01-11",
    goldstein: -3.4,
    mentions: 38,
    actors: ["USAGOV", "GOV"],
  },
];

const ALL_EVENTS: NewsEvent[] = [...(MOCK_NEWS_EVENTS as unknown as NewsEvent[]), ...EXTRA_EVENTS];

function goldsteinColor(value: number): string {
  if (value <= -4) return "var(--danger)";
  if (value < 0) return "#F97316";
  if (value === 0) return "var(--text-muted)";
  return "var(--success)";
}

function GoldsteinIcon({ value }: { value: number }) {
  if (value < 0) return <TrendingDown className="h-4 w-4" style={{ color: goldsteinColor(value) }} />;
  if (value > 0) return <TrendingUp className="h-4 w-4" style={{ color: goldsteinColor(value) }} />;
  return <Minus className="h-4 w-4" style={{ color: goldsteinColor(value) }} />;
}

function ToneBar({ value }: { value: number }) {
  // value range: -10 to +10, center is 0
  const pct = ((value + 10) / 20) * 100;
  const barColor = value < 0 ? "var(--danger)" : "var(--success)";
  const isNeg = value < 0;

  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] font-mono text-[var(--text-muted)] w-8 text-right">
        {value > 0 ? "+" : ""}{value.toFixed(1)}
      </span>
      <div className="relative h-2 w-32 rounded-full bg-[var(--border)]">
        {/* Center marker */}
        <div className="absolute left-1/2 top-0 h-full w-px bg-[var(--text-muted)]" />
        {/* Bar from center */}
        {isNeg ? (
          <div
            className="absolute top-0 h-full rounded-full"
            style={{
              right: "50%",
              width: `${50 - pct}%`,
              backgroundColor: barColor,
            }}
          />
        ) : (
          <div
            className="absolute top-0 h-full rounded-full"
            style={{
              left: "50%",
              width: `${pct - 50}%`,
              backgroundColor: barColor,
            }}
          />
        )}
      </div>
    </div>
  );
}

export default function NewsPage() {
  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--success)]/15">
            <Newspaper className="h-5 w-5 text-[var(--success)]" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">
              News Events
            </h1>
            <p className="text-sm text-[var(--text-secondary)]">
              Global immigration enforcement events via GDELT Project (15-minute updates)
            </p>
          </div>
        </div>

        {/* Live Indicator */}
        <div className="mt-4 flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-live-pulse rounded-full bg-[var(--success)] opacity-75" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-[var(--success)]" />
          </span>
          <span className="text-xs font-medium text-[var(--success)]">
            Updated every 15 minutes
          </span>
        </div>
      </div>

      {/* Stats Row */}
      <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
          <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] mb-1">
            <Globe className="h-3.5 w-3.5" />
            Events Tracked
          </div>
          <div className="text-2xl font-bold text-[var(--foreground)]">1.2M</div>
        </div>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
          <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] mb-1">
            <Radio className="h-3.5 w-3.5" />
            New Today
          </div>
          <div className="text-2xl font-bold text-[var(--success)]">42</div>
        </div>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 col-span-2 sm:col-span-1">
          <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] mb-1">
            <TrendingDown className="h-3.5 w-3.5" />
            Avg Tone
          </div>
          <div className="text-2xl font-bold text-[var(--danger)]">-2.8</div>
        </div>
      </div>

      {/* Event Cards */}
      <div className="space-y-4">
        {ALL_EVENTS.map((event) => (
          <div
            key={event.id}
            className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 transition-colors hover:bg-[var(--surface-hover)]"
          >
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              {/* Left side */}
              <div className="flex-1">
                {/* Source and Date */}
                <div className="flex flex-wrap items-center gap-3 mb-2">
                  <span className="text-xs font-semibold text-[var(--success)]">
                    {event.source}
                  </span>
                  <span className="text-xs text-[var(--text-muted)]">
                    {new Date(event.date).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </span>
                </div>

                {/* Title */}
                <h3 className="text-base font-semibold text-[var(--foreground)] mb-3">
                  {event.title}
                </h3>

                {/* Actor Chips */}
                <div className="flex flex-wrap items-center gap-2">
                  {event.actors.map((actor) => (
                    <span
                      key={actor}
                      className="inline-flex items-center rounded-full border border-[var(--border)] bg-[var(--surface-hover)] px-2.5 py-0.5 font-mono text-[10px] font-medium text-[var(--text-secondary)]"
                    >
                      {actor}
                    </span>
                  ))}
                </div>
              </div>

              {/* Right side: metrics */}
              <div className="flex flex-col items-end gap-3 sm:min-w-[200px]">
                {/* Goldstein Scale */}
                <div className="flex items-center gap-2">
                  <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">
                    Goldstein
                  </span>
                  <GoldsteinIcon value={event.goldstein} />
                  <span
                    className="font-mono text-sm font-bold"
                    style={{ color: goldsteinColor(event.goldstein) }}
                  >
                    {event.goldstein > 0 ? "+" : ""}
                    {event.goldstein.toFixed(1)}
                  </span>
                </div>

                {/* Mentions */}
                <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
                  <MessageSquare className="h-3.5 w-3.5 text-[var(--text-muted)]" />
                  {event.mentions} mentions
                </div>

                {/* Tone Bar */}
                <ToneBar value={event.goldstein} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
