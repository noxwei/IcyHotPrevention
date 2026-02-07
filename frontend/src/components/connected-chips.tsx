"use client";

import Link from "next/link";
import { ExternalLink } from "lucide-react";

const sourceColors: Record<string, string> = {
  contracts: "#F59E0B",
  sec: "#4F8EF7",
  legal: "#8B5CF6",
  news: "#10B981",
  flights: "#EF4444",
};

interface Connection {
  label: string;
  href: string;
  source: "contracts" | "sec" | "legal" | "news" | "flights";
}

interface ConnectedChipsProps {
  connections: Connection[];
}

export default function ConnectedChips({ connections }: ConnectedChipsProps) {
  if (connections.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs font-medium text-[var(--text-muted)]">
        Connected:
      </span>

      {connections.map((conn) => {
        const color = sourceColors[conn.source];

        return (
          <Link
            key={`${conn.source}-${conn.href}`}
            href={conn.href}
            className="group inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-all hover:scale-105"
            style={{
              backgroundColor: `${color}15`,
              color: color,
              borderWidth: "1px",
              borderColor: `${color}30`,
            }}
          >
            {conn.label}
            <ExternalLink className="h-3 w-3 opacity-0 transition-opacity group-hover:opacity-100" />
          </Link>
        );
      })}
    </div>
  );
}
