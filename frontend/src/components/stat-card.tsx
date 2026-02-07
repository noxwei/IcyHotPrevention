"use client";

import type { LucideIcon } from "lucide-react";
import { TrendingUp, TrendingDown } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon: LucideIcon;
  trend?: string;
  trendUp?: boolean;
}

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendUp,
}: StatCardProps) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 transition-colors hover:bg-[var(--surface-hover)]">
      {/* Icon */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--primary)]/15">
          <Icon className="h-5 w-5 text-[var(--primary)]" />
        </div>

        {trend && (
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${
              trendUp
                ? "bg-[var(--success)]/15 text-[var(--success)]"
                : "bg-[var(--danger)]/15 text-[var(--danger)]"
            }`}
          >
            {trendUp ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
            {trend}
          </span>
        )}
      </div>

      {/* Value */}
      <div className="text-3xl font-bold tracking-tight text-[var(--foreground)]">
        {value}
      </div>

      {/* Title */}
      <div className="mt-1 text-sm text-[var(--text-secondary)]">{title}</div>

      {/* Subtitle */}
      {subtitle && (
        <div className="mt-1 text-xs text-[var(--text-muted)]">{subtitle}</div>
      )}
    </div>
  );
}
