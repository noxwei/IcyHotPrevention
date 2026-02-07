"use client";

import { useState } from "react";
import { Plane, Radio, MapPin, Clock, ArrowUp, Navigation } from "lucide-react";
import { TRACKED_AIRCRAFT } from "@/lib/constants";
import FlightMapPlaceholder from "@/components/flight-map-placeholder";

// ---------------------------------------------------------------------------
// Mock position data for airborne aircraft
// ---------------------------------------------------------------------------
const aircraftWithPositions = TRACKED_AIRCRAFT.map((ac) => {
  const positions: Record<
    string,
    { lat: number; lng: number; altitude: number; heading: number }
  > = {
    N368CA: { lat: 29.5, lng: -98.5, altitude: 35000, heading: 180 },
    N406SW: { lat: 33.4, lng: -112.0, altitude: 28000, heading: 270 },
    N802WA: { lat: 25.8, lng: -80.3, altitude: 31000, heading: 45 },
  };

  const pos = positions[ac.registration];
  return {
    ...ac,
    ...(pos ?? {}),
  };
});

// ---------------------------------------------------------------------------
// Mock ground locations for grounded aircraft
// ---------------------------------------------------------------------------
const groundLocations: Record<string, string> = {
  N391CS: "San Antonio, TX",
  N407SW: "Mesa, AZ",
  N408SW: "Houston, TX",
  N803WA: "Miami, FL",
};

// ---------------------------------------------------------------------------
// Mock flight activity observations (last ~2 hours, ~15 min intervals)
// ---------------------------------------------------------------------------
function recentTime(minutesAgo: number): string {
  const d = new Date(Date.now() - minutesAgo * 60_000);
  return d.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

const flightActivity = [
  {
    time: recentTime(5),
    registration: "N368CA",
    callsign: "LCH368",
    lat: "29.50",
    lng: "-98.50",
    altitude: 35000,
    speed: 462,
    heading: 180,
    status: "airborne" as const,
  },
  {
    time: recentTime(15),
    registration: "N406SW",
    callsign: "WQ406",
    lat: "33.40",
    lng: "-112.00",
    altitude: 28000,
    speed: 445,
    heading: 270,
    status: "airborne" as const,
  },
  {
    time: recentTime(20),
    registration: "N802WA",
    callsign: "WAL802",
    lat: "25.80",
    lng: "-80.30",
    altitude: 31000,
    speed: 438,
    heading: 45,
    status: "airborne" as const,
  },
  {
    time: recentTime(30),
    registration: "N368CA",
    callsign: "LCH368",
    lat: "30.12",
    lng: "-98.22",
    altitude: 34200,
    speed: 458,
    heading: 182,
    status: "airborne" as const,
  },
  {
    time: recentTime(45),
    registration: "N406SW",
    callsign: "WQ406",
    lat: "33.10",
    lng: "-111.20",
    altitude: 27500,
    speed: 440,
    heading: 268,
    status: "airborne" as const,
  },
  {
    time: recentTime(60),
    registration: "N802WA",
    callsign: "WAL802",
    lat: "25.40",
    lng: "-80.80",
    altitude: 30500,
    speed: 435,
    heading: 48,
    status: "airborne" as const,
  },
  {
    time: recentTime(75),
    registration: "N368CA",
    callsign: "LCH368",
    lat: "30.80",
    lng: "-97.90",
    altitude: 33800,
    speed: 452,
    heading: 185,
    status: "airborne" as const,
  },
  {
    time: recentTime(90),
    registration: "N406SW",
    callsign: "WQ406",
    lat: "32.75",
    lng: "-110.40",
    altitude: 26800,
    speed: 442,
    heading: 265,
    status: "airborne" as const,
  },
  {
    time: recentTime(105),
    registration: "N802WA",
    callsign: "WAL802",
    lat: "25.05",
    lng: "-81.20",
    altitude: 29800,
    speed: 430,
    heading: 50,
    status: "airborne" as const,
  },
  {
    time: recentTime(120),
    registration: "N368CA",
    callsign: "LCH368",
    lat: "31.45",
    lng: "-97.50",
    altitude: 22000,
    speed: 380,
    heading: 188,
    status: "airborne" as const,
  },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function headingToCompass(deg: number): string {
  const dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  return dirs[Math.round(deg / 45) % 8];
}

// ===========================================================================
// Page Component
// ===========================================================================
export default function FlightsPage() {
  const [viewMode, setViewMode] = useState<"map" | "list">("map");

  const airborneCount = TRACKED_AIRCRAFT.filter(
    (a) => a.status === "airborne"
  ).length;

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      {/* ----------------------------------------------------------------- */}
      {/* 1. Page Header                                                    */}
      {/* ----------------------------------------------------------------- */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">
              Flight Tracker
            </h1>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-[var(--success)]/15 px-3 py-1 text-xs font-semibold text-[var(--success)]">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[var(--success)] opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-[var(--success)]" />
              </span>
              LIVE
            </span>
          </div>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">
            Real-time tracking of known ICE charter aircraft via OpenSky Network
          </p>
        </div>

        {/* View toggle */}
        <div className="flex items-center rounded-lg border border-[var(--border)] bg-[var(--surface)] p-1">
          <button
            onClick={() => setViewMode("map")}
            className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
              viewMode === "map"
                ? "bg-[var(--primary)] text-white"
                : "text-[var(--text-secondary)] hover:text-[var(--foreground)]"
            }`}
          >
            Map View
          </button>
          <button
            onClick={() => setViewMode("list")}
            className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
              viewMode === "list"
                ? "bg-[var(--primary)] text-white"
                : "text-[var(--text-secondary)] hover:text-[var(--foreground)]"
            }`}
          >
            List View
          </button>
        </div>
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* 2. Flight Map                                                     */}
      {/* ----------------------------------------------------------------- */}
      <section className="mb-8">
        <FlightMapPlaceholder aircraft={aircraftWithPositions} />
      </section>

      {/* ----------------------------------------------------------------- */}
      {/* 3. Aircraft Status Cards (horizontally scrollable)                */}
      {/* ----------------------------------------------------------------- */}
      <section className="mb-8">
        <h2 className="mb-4 text-lg font-semibold text-[var(--foreground)]">
          Aircraft Status
        </h2>
        <div className="flex gap-4 overflow-x-auto pb-2">
          {TRACKED_AIRCRAFT.map((ac) => {
            const isAirborne = ac.status === "airborne";
            const pos = aircraftWithPositions.find(
              (a) => a.registration === ac.registration
            );
            const groundLoc = groundLocations[ac.registration];

            return (
              <div
                key={ac.registration}
                className={`flex w-64 shrink-0 flex-col gap-3 rounded-xl border bg-[var(--surface)] p-4 transition-colors hover:bg-[var(--surface-hover)] ${
                  isAirborne
                    ? "animate-glow border-[var(--accent)]/50"
                    : "border-[var(--border)]"
                }`}
              >
                {/* Registration + Status */}
                <div className="flex items-center justify-between">
                  <span className="font-mono text-lg font-bold text-[var(--foreground)]">
                    {ac.registration}
                  </span>
                  {isAirborne ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-[var(--success)]/15 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-[var(--success)]">
                      <Navigation className="h-3 w-3" />
                      Airborne
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 rounded-full bg-[var(--text-muted)]/15 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                      <MapPin className="h-3 w-3" />
                      On Ground
                    </span>
                  )}
                </div>

                {/* Operator + Type */}
                <div>
                  <div className="text-sm text-[var(--text-secondary)]">
                    {ac.operator}
                  </div>
                  <div className="text-xs text-[var(--text-muted)]">
                    {ac.type}
                  </div>
                </div>

                {/* Airborne details or ground location */}
                {isAirborne && pos && "altitude" in pos ? (
                  <div className="flex items-center gap-4 rounded-lg bg-[var(--background)]/60 px-3 py-2">
                    <div className="flex items-center gap-1 text-xs text-[var(--text-secondary)]">
                      <ArrowUp className="h-3 w-3 text-[var(--accent)]" />
                      <span className="font-mono">
                        {(pos.altitude as number).toLocaleString()} ft
                      </span>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-[var(--text-secondary)]">
                      <Navigation
                        className="h-3 w-3 text-[var(--accent)]"
                        style={{
                          transform: `rotate(${pos.heading as number}deg)`,
                        }}
                      />
                      <span className="font-mono">
                        {pos.heading as number}° {headingToCompass(pos.heading as number)}
                      </span>
                    </div>
                  </div>
                ) : groundLoc ? (
                  <div className="flex items-center gap-2 rounded-lg bg-[var(--background)]/60 px-3 py-2 text-xs text-[var(--text-muted)]">
                    <MapPin className="h-3 w-3" />
                    Last seen: {groundLoc}
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      </section>

      {/* ----------------------------------------------------------------- */}
      {/* 4. Flight Activity Table                                          */}
      {/* ----------------------------------------------------------------- */}
      <section className="mb-8">
        <h2 className="mb-4 text-lg font-semibold text-[var(--foreground)]">
          Recent Flight Activity
        </h2>
        <div className="overflow-x-auto rounded-xl border border-[var(--border)]">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] bg-[var(--surface)]">
                <th className="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                  Time
                </th>
                <th className="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                  Registration
                </th>
                <th className="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                  Callsign
                </th>
                <th className="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                  Position
                </th>
                <th className="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                  Altitude
                </th>
                <th className="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                  Speed
                </th>
                <th className="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                  Heading
                </th>
                <th className="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {flightActivity.map((row, idx) => (
                <tr
                  key={`${row.registration}-${row.time}-${idx}`}
                  className={`border-b border-[var(--border)] transition-colors hover:bg-[var(--surface-hover)] ${
                    idx % 2 === 0 ? "bg-[var(--background)]" : "bg-[var(--surface)]/40"
                  }`}
                >
                  <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-[var(--text-secondary)]">
                    {row.time}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 font-mono font-semibold text-[var(--foreground)]">
                    {row.registration}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-[var(--text-secondary)]">
                    {row.callsign}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-[var(--text-muted)]">
                    {row.lat}, {row.lng}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-[var(--text-secondary)]">
                    {row.altitude.toLocaleString()} ft
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-[var(--text-secondary)]">
                    {row.speed} kts
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-xs text-[var(--text-secondary)]">
                    <span className="inline-flex items-center gap-1 font-mono">
                      <Navigation
                        className="h-3 w-3 text-[var(--accent)]"
                        style={{ transform: `rotate(${row.heading}deg)` }}
                      />
                      {row.heading}°
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    <span className="inline-flex items-center gap-1 rounded-full bg-[var(--success)]/15 px-2 py-0.5 text-[10px] font-semibold uppercase text-[var(--success)]">
                      <span className="h-1.5 w-1.5 rounded-full bg-[var(--success)]" />
                      Airborne
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ----------------------------------------------------------------- */}
      {/* 5. Stats Bar                                                      */}
      {/* ----------------------------------------------------------------- */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="flex items-center gap-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] px-5 py-4 transition-colors hover:bg-[var(--surface-hover)]">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--primary)]/15">
            <Plane className="h-5 w-5 text-[var(--primary)]" />
          </div>
          <div>
            <div className="text-2xl font-bold tracking-tight text-[var(--foreground)]">
              {TRACKED_AIRCRAFT.length}
            </div>
            <div className="text-sm text-[var(--text-secondary)]">
              Aircraft Tracked
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] px-5 py-4 transition-colors hover:bg-[var(--surface-hover)]">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--success)]/15">
            <Radio className="h-5 w-5 text-[var(--success)]" />
          </div>
          <div>
            <div className="text-2xl font-bold tracking-tight text-[var(--foreground)]">
              {airborneCount}
            </div>
            <div className="text-sm text-[var(--text-secondary)]">
              Currently Airborne
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] px-5 py-4 transition-colors hover:bg-[var(--surface-hover)]">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--accent)]/15">
            <Clock className="h-5 w-5 text-[var(--accent)]" />
          </div>
          <div>
            <div className="text-2xl font-bold tracking-tight text-[var(--foreground)]">
              10s ago
            </div>
            <div className="text-sm text-[var(--text-secondary)]">
              Last Update
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
