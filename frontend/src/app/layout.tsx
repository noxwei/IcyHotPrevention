import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Nav from "@/components/nav";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "IETY - Immigration Enforcement Transparency",
  description:
    "Tracking federal contracts, corporate filings, legal proceedings, news events, and charter aircraft across 5 public data sources.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <Nav />
        <main>{children}</main>
        <footer className="border-t border-[var(--border)] py-8">
          <div className="mx-auto max-w-7xl px-6">
            <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
              <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
                <div className="flex h-5 w-5 items-center justify-center rounded bg-[var(--primary)]">
                  <span className="font-mono text-[8px] font-bold text-white">IE</span>
                </div>
                IETY - Immigration Enforcement Transparency
              </div>
              <div className="flex gap-6 text-sm text-[var(--text-muted)]">
                <a href="/about" className="hover:text-[var(--text-secondary)]">Methodology</a>
                <a href="/about" className="hover:text-[var(--text-secondary)]">Data Sources</a>
                <a href="/api" className="hover:text-[var(--text-secondary)]">API</a>
              </div>
            </div>
            <p className="mt-4 text-center text-xs text-[var(--text-muted)] sm:text-left">
              All data sourced from public federal databases. This is a transparency tool, not legal advice.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
