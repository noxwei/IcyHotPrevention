"use client";

const sourceConfig: Record<
  string,
  { label: string; color: string }
> = {
  contracts: { label: "CONTRACTS", color: "#F59E0B" },
  sec: { label: "SEC", color: "#4F8EF7" },
  legal: { label: "LEGAL", color: "#8B5CF6" },
  news: { label: "NEWS", color: "#10B981" },
  flights: { label: "FLIGHTS", color: "#EF4444" },
};

interface SourceBadgeProps {
  source: "contracts" | "sec" | "legal" | "news" | "flights";
}

export default function SourceBadge({ source }: SourceBadgeProps) {
  const config = sourceConfig[source];

  return (
    <span
      className="inline-flex items-center rounded-full px-2.5 py-0.5 font-semibold leading-none"
      style={{
        fontSize: "10px",
        letterSpacing: "0.05em",
        backgroundColor: `${config.color}26`,
        color: config.color,
      }}
    >
      {config.label}
    </span>
  );
}
