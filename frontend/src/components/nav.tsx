"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  Search,
  ChevronDown,
  DollarSign,
  Building2,
  Scale,
  Newspaper,
  Plane,
  Menu,
  X,
} from "lucide-react";

const exploreLinks = [
  { label: "Contracts", href: "/explore/contracts", icon: DollarSign, desc: "Federal spending on enforcement" },
  { label: "Corporate", href: "/explore/corporate", icon: Building2, desc: "SEC filings from contractors" },
  { label: "Legal", href: "/explore/legal", icon: Scale, desc: "Immigration court cases" },
  { label: "News", href: "/explore/news", icon: Newspaper, desc: "Global events via GDELT" },
  { label: "Flights", href: "/explore/flights", icon: Plane, desc: "ICE charter aircraft tracking" },
];

export default function Nav() {
  const pathname = usePathname();
  const [exploreOpen, setExploreOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const isExplore = pathname.startsWith("/explore");

  return (
    <nav className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--background)]/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--primary)]">
            <span className="font-mono text-sm font-bold text-white">IE</span>
          </div>
          <span className="text-lg font-semibold tracking-tight">IETY</span>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden items-center gap-1 md:flex">
          <Link
            href="/"
            className={`rounded-lg px-3 py-2 text-sm transition-colors ${
              pathname === "/"
                ? "bg-[var(--surface)] text-white"
                : "text-[var(--text-secondary)] hover:text-white"
            }`}
          >
            Home
          </Link>

          {/* Explore Dropdown */}
          <div
            className="relative"
            onMouseEnter={() => setExploreOpen(true)}
            onMouseLeave={() => setExploreOpen(false)}
          >
            <button
              className={`flex items-center gap-1 rounded-lg px-3 py-2 text-sm transition-colors ${
                isExplore
                  ? "bg-[var(--surface)] text-white"
                  : "text-[var(--text-secondary)] hover:text-white"
              }`}
            >
              Explore
              <ChevronDown className={`h-3.5 w-3.5 transition-transform ${exploreOpen ? "rotate-180" : ""}`} />
            </button>

            {exploreOpen && (
              <div className="absolute left-0 top-full mt-1 w-72 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-2 shadow-2xl">
                {exploreLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`flex items-start gap-3 rounded-lg px-3 py-2.5 transition-colors ${
                      pathname === link.href
                        ? "bg-[var(--surface-hover)] text-white"
                        : "text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-white"
                    }`}
                    onClick={() => setExploreOpen(false)}
                  >
                    <link.icon className="mt-0.5 h-4 w-4 shrink-0 text-[var(--primary)]" />
                    <div>
                      <div className="text-sm font-medium">{link.label}</div>
                      <div className="text-xs text-[var(--text-muted)]">{link.desc}</div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          <Link
            href="/search"
            className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm transition-colors ${
              pathname === "/search"
                ? "bg-[var(--surface)] text-white"
                : "text-[var(--text-secondary)] hover:text-white"
            }`}
          >
            <Search className="h-3.5 w-3.5" />
            Search
          </Link>

          <Link
            href="/about"
            className={`rounded-lg px-3 py-2 text-sm transition-colors ${
              pathname === "/about"
                ? "bg-[var(--surface)] text-white"
                : "text-[var(--text-secondary)] hover:text-white"
            }`}
          >
            About
          </Link>
        </div>

        {/* Right side */}
        <div className="hidden items-center gap-3 md:flex">
          <Link
            href="/search"
            className="flex h-9 items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--text-muted)] transition-colors hover:border-[var(--primary)]/50 hover:text-[var(--text-secondary)]"
          >
            <Search className="h-3.5 w-3.5" />
            <span>Search all sources...</span>
            <kbd className="ml-6 rounded border border-[var(--border)] px-1.5 py-0.5 font-mono text-[10px]">/</kbd>
          </Link>
          <a
            href="/api"
            className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm text-[var(--text-secondary)] transition-colors hover:border-[var(--primary)] hover:text-[var(--primary)]"
          >
            API
          </a>
        </div>

        {/* Mobile hamburger */}
        <button
          className="rounded-lg p-2 text-[var(--text-secondary)] md:hidden"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="border-t border-[var(--border)] bg-[var(--surface)] px-6 py-4 md:hidden">
          <div className="flex flex-col gap-1">
            <Link href="/" className="rounded-lg px-3 py-2 text-sm text-[var(--text-secondary)] hover:text-white" onClick={() => setMobileOpen(false)}>Home</Link>
            <div className="px-3 py-2 text-xs font-medium uppercase tracking-wider text-[var(--text-muted)]">Explore</div>
            {exploreLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="flex items-center gap-2 rounded-lg px-3 py-2 pl-6 text-sm text-[var(--text-secondary)] hover:text-white"
                onClick={() => setMobileOpen(false)}
              >
                <link.icon className="h-4 w-4 text-[var(--primary)]" />
                {link.label}
              </Link>
            ))}
            <Link href="/search" className="rounded-lg px-3 py-2 text-sm text-[var(--text-secondary)] hover:text-white" onClick={() => setMobileOpen(false)}>Search</Link>
            <Link href="/about" className="rounded-lg px-3 py-2 text-sm text-[var(--text-secondary)] hover:text-white" onClick={() => setMobileOpen(false)}>About</Link>
          </div>
        </div>
      )}
    </nav>
  );
}
