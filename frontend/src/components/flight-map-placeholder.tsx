"use client";

import { useMemo } from "react";
import { Plane, MapPin } from "lucide-react";

interface Aircraft {
  registration: string;
  operator: string;
  type: string;
  status: "airborne" | "ground";
  lat?: number;
  lng?: number;
  altitude?: number;
  heading?: number;
}

interface FlightMapPlaceholderProps {
  aircraft: Aircraft[];
}

/* Simplified US continental outline as an SVG path */
const US_OUTLINE =
  "M 80 55 L 90 48 L 105 46 L 120 48 L 138 42 L 155 40 L 170 42 L 185 38 " +
  "L 200 35 L 218 37 L 235 32 L 250 30 L 268 28 L 280 30 L 295 35 L 310 38 " +
  "L 325 40 L 340 38 L 355 35 L 370 37 L 385 40 L 395 45 L 405 50 L 412 58 " +
  "L 418 68 L 420 78 L 418 88 L 412 98 L 405 105 L 398 110 L 388 115 " +
  "L 375 118 L 360 120 L 345 118 L 330 122 L 315 128 L 298 132 L 280 135 " +
  "L 262 138 L 245 140 L 228 138 L 210 140 L 192 138 L 175 140 L 158 142 " +
  "L 140 140 L 122 138 L 105 140 L 88 138 L 75 132 L 68 122 L 65 112 " +
  "L 62 100 L 60 88 L 62 78 L 65 68 L 70 60 Z";

/**
 * Seeded pseudo-random number generator so dot positions are
 * deterministic across renders for aircraft without lat/lng.
 */
function seededRandom(seed: string): () => number {
  let h = 0;
  for (let i = 0; i < seed.length; i++) {
    h = (Math.imul(31, h) + seed.charCodeAt(i)) | 0;
  }
  return () => {
    h = (Math.imul(h ^ (h >>> 16), 0x45d9f3b) + 0x9e3779b9) | 0;
    return ((h >>> 0) / 0xffffffff) * 0.6 + 0.2; // clamp 0.2 - 0.8
  };
}

function aircraftPosition(
  ac: Aircraft,
  idx: number,
): { x: number; y: number } {
  if (ac.lat != null && ac.lng != null) {
    // Map lat/lng roughly to SVG viewBox (480 x 180)
    // US roughly: lat 24-50, lng -125 to -66
    const x = ((ac.lng + 125) / 59) * 380 + 50;
    const y = ((50 - ac.lat) / 26) * 130 + 20;
    return {
      x: Math.max(60, Math.min(420, x)),
      y: Math.max(25, Math.min(145, y)),
    };
  }

  // Deterministic pseudo-random placement inside map area
  const rng = seededRandom(`${ac.registration}-${idx}`);
  return {
    x: rng() * 360 + 60,
    y: rng() * 110 + 30,
  };
}

export default function FlightMapPlaceholder({
  aircraft,
}: FlightMapPlaceholderProps) {
  const airborneCount = aircraft.filter((a) => a.status === "airborne").length;
  const groundCount = aircraft.filter((a) => a.status === "ground").length;

  const positions = useMemo(
    () => aircraft.map((ac, i) => ({ ac, pos: aircraftPosition(ac, i) })),
    [aircraft],
  );

  return (
    <div className="relative overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--surface)]">
      {/* Inline keyframes for pulsing and trail animations */}
      <style>{`
        @keyframes flight-pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.6; transform: scale(1.8); }
        }
        @keyframes flight-trail {
          0% { stroke-dashoffset: 0; }
          100% { stroke-dashoffset: -20; }
        }
        @keyframes flight-radar {
          0% { opacity: 0.4; r: 6; }
          100% { opacity: 0; r: 18; }
        }
      `}</style>

      {/* Map SVG */}
      <svg
        viewBox="0 0 480 180"
        className="h-full w-full"
        style={{ minHeight: "320px" }}
        preserveAspectRatio="xMidYMid meet"
      >
        {/* Background gradient */}
        <defs>
          <radialGradient id="map-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.08" />
            <stop offset="100%" stopColor="transparent" stopOpacity="0" />
          </radialGradient>
          <filter id="dot-glow">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Glow behind map */}
        <rect x="0" y="0" width="480" height="180" fill="url(#map-glow)" />

        {/* Grid lines for visual interest */}
        {Array.from({ length: 9 }).map((_, i) => (
          <line
            key={`vg-${i}`}
            x1={50 + i * 47.5}
            y1="20"
            x2={50 + i * 47.5}
            y2="155"
            stroke="var(--border)"
            strokeWidth="0.3"
            strokeDasharray="2 4"
          />
        ))}
        {Array.from({ length: 6 }).map((_, i) => (
          <line
            key={`hg-${i}`}
            x1="50"
            y1={20 + i * 27}
            x2="430"
            y2={20 + i * 27}
            stroke="var(--border)"
            strokeWidth="0.3"
            strokeDasharray="2 4"
          />
        ))}

        {/* US outline */}
        <path
          d={US_OUTLINE}
          fill="none"
          stroke="var(--text-muted)"
          strokeWidth="1"
          strokeOpacity="0.35"
          strokeLinejoin="round"
        />

        {/* Subtle fill */}
        <path
          d={US_OUTLINE}
          fill="var(--primary)"
          fillOpacity="0.04"
          strokeLinejoin="round"
        />

        {/* Aircraft dots */}
        {positions.map(({ ac, pos }, i) => {
          const isAirborne = ac.status === "airborne";
          const heading = ac.heading ?? (i * 47) % 360;
          const trailRad = ((heading + 180) * Math.PI) / 180;
          const trailEndX = pos.x + Math.cos(trailRad) * 18;
          const trailEndY = pos.y + Math.sin(trailRad) * 18;

          return (
            <g key={ac.registration || i}>
              {isAirborne && (
                <>
                  {/* Amber trail line */}
                  <line
                    x1={pos.x}
                    y1={pos.y}
                    x2={trailEndX}
                    y2={trailEndY}
                    stroke="#F59E0B"
                    strokeWidth="1.5"
                    strokeOpacity="0.5"
                    strokeLinecap="round"
                    strokeDasharray="3 3"
                    style={{
                      animation: "flight-trail 0.8s linear infinite",
                    }}
                  />

                  {/* Radar ring */}
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r="6"
                    fill="none"
                    stroke="#10B981"
                    strokeWidth="0.8"
                    style={{
                      animation: "flight-radar 2s ease-out infinite",
                      animationDelay: `${(i * 400) % 2000}ms`,
                    }}
                  />

                  {/* Pulsing glow */}
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r="4"
                    fill="#10B981"
                    fillOpacity="0.25"
                    style={{
                      animation: "flight-pulse 2s ease-in-out infinite",
                      animationDelay: `${(i * 300) % 2000}ms`,
                      transformOrigin: `${pos.x}px ${pos.y}px`,
                    }}
                  />

                  {/* Core dot - green airborne */}
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r="2.5"
                    fill="#10B981"
                    filter="url(#dot-glow)"
                  />
                </>
              )}

              {!isAirborne && (
                <>
                  {/* Ground - static grey dot */}
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r="2"
                    fill="var(--text-muted)"
                    fillOpacity="0.7"
                  />
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r="3.5"
                    fill="none"
                    stroke="var(--text-muted)"
                    strokeWidth="0.5"
                    strokeOpacity="0.3"
                  />
                </>
              )}

              {/* Registration label for airborne aircraft */}
              {isAirborne && (
                <text
                  x={pos.x + 5}
                  y={pos.y - 5}
                  fontSize="4"
                  fill="var(--text-muted)"
                  fontFamily="monospace"
                  opacity="0.7"
                >
                  {ac.registration}
                </text>
              )}
            </g>
          );
        })}

        {/* "No Mapbox Token" watermark */}
        <text
          x="240"
          y="170"
          textAnchor="middle"
          fontSize="5"
          fill="var(--text-muted)"
          opacity="0.4"
          fontFamily="monospace"
        >
          FLIGHT MAP PREVIEW - Connect Mapbox for full interactivity
        </text>
      </svg>

      {/* Bottom overlay stats bar */}
      <div className="absolute inset-x-0 bottom-0 flex items-center justify-between border-t border-[var(--border)] bg-[var(--background)]/90 px-5 py-3 backdrop-blur-sm">
        <div className="flex items-center gap-4">
          {/* Airborne */}
          <div className="flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-green-500" />
            </span>
            <span className="text-sm font-medium text-[var(--foreground)]">
              {airborneCount}
            </span>
            <span className="text-xs text-[var(--text-muted)]">Airborne</span>
          </div>

          {/* Ground */}
          <div className="flex items-center gap-2">
            <span className="inline-flex h-2.5 w-2.5 rounded-full bg-[var(--text-muted)]" />
            <span className="text-sm font-medium text-[var(--foreground)]">
              {groundCount}
            </span>
            <span className="text-xs text-[var(--text-muted)]">Ground</span>
          </div>

          {/* Total */}
          <div className="flex items-center gap-2 border-l border-[var(--border)] pl-4">
            <Plane className="h-3.5 w-3.5 text-[var(--text-muted)]" />
            <span className="text-sm font-medium text-[var(--foreground)]">
              {aircraft.length}
            </span>
            <span className="text-xs text-[var(--text-muted)]">
              Total Tracked
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
          <MapPin className="h-3 w-3" />
          CONUS
        </div>
      </div>
    </div>
  );
}
