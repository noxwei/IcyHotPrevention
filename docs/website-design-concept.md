# IETY Website Design Concept

## Product Manager Brief

### Vision Statement
IETY makes invisible immigration enforcement spending, contracts, flights, and legal
proceedings visible to researchers, journalists, and the public through a single
searchable platform that connects the dots across five federal data sources.

### Target Personas

| Persona | Need | Key Task |
|---------|------|----------|
| **Investigative Journalist** | Breaking stories on enforcement spending | Search contracts, cross-reference with flights, export citations |
| **Policy Researcher** | Data-driven immigration policy analysis | Filter by fiscal year, compare contractor spending, download datasets |
| **Advocacy Organization** | Track enforcement activity near communities | Real-time flight map, legal case monitoring, alerts |
| **Academic** | Longitudinal studies on enforcement trends | Bulk data access, methodology documentation, API |

### Information Architecture

```
IETY.org
|
+-- Home (Live dashboard: headline stats + map)
|
+-- Explore
|   +-- Contracts (/explore/contracts)      -- USASpending data
|   +-- Corporate (/explore/corporate)      -- SEC filings
|   +-- Legal (/explore/legal)              -- CourtListener cases
|   +-- News (/explore/news)               -- GDELT events
|   +-- Flights (/explore/flights)          -- Real-time aircraft
|
+-- Search (/search)                        -- Unified hybrid search
|
+-- Investigations (/investigations)        -- Curated cross-source stories
|
+-- About (/about)
|   +-- Methodology
|   +-- Data Sources
|   +-- FAQ
|
+-- API Docs (/api)
```

### Core User Flows

**Flow 1: "Follow the Money"**
Home -> Contracts -> Filter by contractor -> See SEC filings for same company
-> See related legal cases -> Export report

**Flow 2: "Track the Flights"**
Home -> Flight Map -> Click aircraft -> See flight history -> Overlay with
ICE facility locations -> Cross-reference with news events on same dates

**Flow 3: "Research a Topic"**
Search bar -> "detention facility conditions" -> Results from all 5 sources,
ranked by relevance -> Filter by source/date -> Save search -> Set alert

---

## Frontend Designer Concept

### Design Principles

1. **Clarity over decoration** -- Data credibility demands clean, restrained design
2. **Progressive disclosure** -- Summary first, detail on demand
3. **Connected data** -- Always show cross-source links visually
4. **Accessible** -- WCAG AA minimum, screen-reader friendly tables and charts
5. **Fast perceived performance** -- Skeleton screens, stream results as they arrive

### Visual Language

**Palette:**
```
Background:     #0F1117  (deep navy-black)
Surface:        #1A1D27  (card background)
Surface-hover:  #242836  (interactive state)
Border:         #2E3348  (subtle separation)

Primary:        #4F8EF7  (trustworthy blue -- links, active states)
Accent:         #F59E0B  (amber -- warnings, highlights, flight paths)
Success:        #10B981  (green -- active/online indicators)
Danger:         #EF4444  (red -- alerts, halted states)

Text-primary:   #E8EAED
Text-secondary: #9CA3AF
Text-muted:     #6B7280
```

Dark theme is the default -- this is a data-heavy investigative tool,
not a marketing site. Dark reduces eye strain for long research sessions.

**Typography:**
```
Headlines:  Inter, 600 weight
Body:       Inter, 400 weight
Data/Code:  JetBrains Mono (tables, dollar amounts, ICAO codes)
```

**Grid:** 12-column, 1280px max-width, 24px gutters

---

### Page Designs

#### 1. HOME -- Live Dashboard

```
+------------------------------------------------------------------------+
|  [IETY logo]          Explore v    Search [_____________] [?]    [API] |
+------------------------------------------------------------------------+
|                                                                        |
|   IMMIGRATION ENFORCEMENT TRANSPARENCY                                 |
|   Tracking $X.XB in federal contracts, XX aircraft,                    |
|   and XX,XXX legal proceedings across 5 public data sources.           |
|                                                                        |
+------------------------------------------------------------------------+
|                                                                        |
|   +-- HERO: LIVE FLIGHT MAP (full-width, Mapbox GL) ---------------+  |
|   |                                                                 |  |
|   |   [ Dark-themed US map with:                                    |  |
|   |     - Amber dotted lines = active flight paths                  |  |
|   |     - Blue pins = ICE facilities                                |  |
|   |     - Pulsing green dots = aircraft currently airborne          |  |
|   |     - Grey dots = aircraft on ground                            |  |
|   |   ]                                                             |  |
|   |                                                                 |  |
|   |   Bottom overlay:                                               |  |
|   |   [7 aircraft tracked] [3 airborne] [Last update: 10s ago]      |  |
|   |                                                                 |  |
|   +-----------------------------------------------------------------+  |
|                                                                        |
+------------------------------------------------------------------------+
|                                                                        |
|   +-- STAT CARDS (4-column grid) ----------------------------------+  |
|   |                                                                 |  |
|   |  +-----------+ +-----------+ +-----------+ +-----------+        |  |
|   |  | $2.54B    | | 8         | | 12,847    | | 1.2M      |        |  |
|   |  | Total     | | Tracked   | | Court     | | News      |        |  |
|   |  | Contracts | | Companies | | Cases     | | Events    |        |  |
|   |  | +12% YoY  | | 3 flagged | | +340 /mo  | | 15min ago |        |  |
|   |  +-----------+ +-----------+ +-----------+ +-----------+        |  |
|   |                                                                 |  |
|   +-----------------------------------------------------------------+  |
|                                                                        |
+------------------------------------------------------------------------+
|                                                                        |
|   +-- RECENT ACTIVITY FEED (2-column) -----------------------------+  |
|   |                                                                 |  |
|   |  LEFT: Latest Contract Awards      RIGHT: Latest Legal Filings  |  |
|   |  +--------------------------+  +-----------------------------+  |  |
|   |  | [amber dot] $45.2M       |  | [blue dot] Doe v. ICE       |  |
|   |  | CoreCivic - Detention    |  | S.D. Texas - Filed 2h ago   |  |
|   |  | services FY2025          |  | Detention conditions claim   |  |
|   |  +--------------------------+  +-----------------------------+  |  |
|   |  | [amber dot] $12.8M       |  | [blue dot] ACLU v. CBP      |  |
|   |  | Palantir - ICE data      |  | D. Arizona - Updated 5h ago |  |
|   |  | systems renewal          |  | FOIA enforcement action      |  |
|   |  +--------------------------+  +-----------------------------+  |  |
|   |                                                                 |  |
|   +-----------------------------------------------------------------+  |
|                                                                        |
+------------------------------------------------------------------------+
|   [View all contracts ->]         [View all cases ->]                  |
+------------------------------------------------------------------------+
```

#### 2. CONTRACTS EXPLORER (/explore/contracts)

```
+------------------------------------------------------------------------+
|  CONTRACTS                                                    [Export]  |
+------------------------------------------------------------------------+
|                                                                        |
|  FILTERS (horizontal bar):                                             |
|  [Fiscal Year v] [Agency v] [Contractor v] [Min $___] [Max $___]      |
|                                                                        |
+------------------------------------------------------------------------+
|                                                                        |
|  +-- TOP CONTRACTORS (horizontal bar chart) -----------------------+  |
|  |                                                                  |  |
|  |  Leidos          ==============================  $892M           |  |
|  |  General Dynamics =======================  $634M                 |  |
|  |  Palantir         =================  $421M                      |  |
|  |  L3Harris          ==============  $312M                        |  |
|  |  Northrop Grumman   ============  $287M                         |  |
|  |  GEO Group           =========  $198M                           |  |
|  |  CoreCivic            ========  $176M                           |  |
|  |                                                                  |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +-- SPENDING OVER TIME (area chart, stacked by contractor) -------+  |
|  |                                                                  |  |
|  |   $M                                                             |  |
|  |  200|       ___                                                  |  |
|  |  150|    __/   \___    ___                                       |  |
|  |  100|___/          \__/   \___                                   |  |
|  |   50|                         \___                               |  |
|  |     +--+--+--+--+--+--+--+--+--+-->                             |  |
|  |     FY18  19  20  21  22  23  24  25                             |  |
|  |                                                                  |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +-- CONTRACT TABLE -----------------------------------------------+  |
|  |  Award ID  | Contractor     | Amount    | Agency | FY   | Desc  |  |
|  |------------|----------------|-----------|--------|------|-------|  |
|  |  HSCEXX... | CoreCivic      | $45.2M    | ICE    | 2025 | Det.. |  |
|  |  HSCEXX... | Palantir Tech  | $12.8M    | ICE    | 2025 | Dat.. |  |
|  |  HSCEXX... | GEO Group      | $8.4M     | ICE    | 2025 | Fac.. |  |
|  |                                                                  |  |
|  |  Each row expandable -> shows full description + links to:       |  |
|  |    [SEC Filings for this company] [Related legal cases] [News]   |  |
|  |                                                                  |  |
|  +------------------------------------------------------------------+  |
```

#### 3. FLIGHT TRACKER (/explore/flights)

```
+------------------------------------------------------------------------+
|  FLIGHT TRACKER                               [List View] [Map View]   |
+------------------------------------------------------------------------+
|                                                                        |
|  +-- FULL-WIDTH MAP (70vh) ----------------------------------------+  |
|  |                                                                  |  |
|  |   [ Mapbox dark map, full US view                                |  |
|  |     - Animated amber arcs for active flights                     |  |
|  |     - Aircraft icons rotate to match heading                     |  |
|  |     - Click aircraft -> popup with details                       |  |
|  |     - Blue markers for known ICE facilities                      |  |
|  |     - Trail lines showing last 2h of movement                   |  |
|  |   ]                                                              |  |
|  |                                                                  |  |
|  |   Popup on click:                                                |  |
|  |   +-----------------------------+                                |  |
|  |   | N368CA - Classic Air Charter|                                |  |
|  |   | B737 | Alt: 35,000ft        |                                |  |
|  |   | Speed: 450kts | Hdg: 180   |                                |  |
|  |   | [View flight history ->]    |                                |  |
|  |   +-----------------------------+                                |  |
|  |                                                                  |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +-- AIRCRAFT STATUS CARDS (scrollable row) -----------------------+  |
|  |                                                                  |  |
|  |  +-- N368CA -----+  +-- N406SW -----+  +-- N802WA -----+       |  |
|  |  | Classic Air   |  | iAero Airways |  | World Atlantic |       |  |
|  |  | B737          |  | B737          |  | MD-83          |       |  |
|  |  | [green] AIRB  |  | [green] AIRB  |  | [grey] GRND    |       |  |
|  |  | 35,000ft 450k |  | 28,000ft 380k |  | San Antonio TX |       |  |
|  |  +---------------+  +---------------+  +----------------+       |  |
|  |                                                                  |  |
|  +------------------------------------------------------------------+  |
```

#### 4. UNIFIED SEARCH (/search)

```
+------------------------------------------------------------------------+
|                                                                        |
|         [___________________________________________________]          |
|         [ Search across contracts, filings, cases, and news ]          |
|                                                                        |
|  Source filter chips:                                                   |
|  [x All] [ Contracts] [ SEC Filings] [ Legal] [ News] [ Flights]      |
|                                                                        |
|  Sort: [Relevance v]  Date: [Any time v]                               |
|                                                                        |
+------------------------------------------------------------------------+
|                                                                        |
|  Results for "detention facility conditions"         1,247 results     |
|                                                                        |
|  +-- RESULT CARD --------------------------------------------------+  |
|  |  [LEGAL]  Doe v. ICE, Case No. 4:24-cv-01234                    |  |
|  |  S.D. Texas | Filed Jan 15, 2025 | Deportation (NOS 462)        |  |
|  |                                                                  |  |
|  |  "...allegations of inadequate medical care at the [detention    |  |
|  |  facility] operated by CoreCivic under contract HSCE..."         |  |
|  |                                                                  |  |
|  |  Connected: [CoreCivic SEC Filing] [Contract HSCE-24-0012]       |  |
|  |  Relevance: 0.94                                                 |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +-- RESULT CARD --------------------------------------------------+  |
|  |  [CONTRACT]  CoreCivic - Detention Services, $45.2M              |  |
|  |  ICE | FY2025 | TAS 070-0540                                     |  |
|  |                                                                  |  |
|  |  "Immigration detention facility operations and maintenance      |  |
|  |  services at South Texas Processing Center..."                   |  |
|  |                                                                  |  |
|  |  Connected: [3 legal cases] [SEC 10-Q filing] [12 news events]   |  |
|  |  Relevance: 0.91                                                 |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  +-- RESULT CARD --------------------------------------------------+  |
|  |  [NEWS]  "ICE detention center faces scrutiny over conditions"   |  |
|  |  GDELT | Jan 12, 2025 | Goldstein: -4.2 | 28 mentions           |  |
|  |                                                                  |  |
|  |  Source: Reuters | Actors: USAGOV, NGO                           |  |
|  |                                                                  |  |
|  |  Connected: [Related contract] [2 legal cases]                   |  |
|  |  Relevance: 0.87                                                 |  |
|  +------------------------------------------------------------------+  |
```

#### 5. CORPORATE DEEP-DIVE (/explore/corporate/:company)

```
+------------------------------------------------------------------------+
|  < Back to Companies                                                   |
+------------------------------------------------------------------------+
|                                                                        |
|  GEO GROUP INC                                        CIK: 0000923796 |
|  Private prison and detention facility operator                        |
|  [SEC EDGAR ->] [USASpending ->]                                       |
|                                                                        |
+------------------------------------------------------------------------+
|                                                                        |
|  +-- FINANCIAL OVERVIEW (sparkline cards) -------------------------+  |
|  |                                                                  |  |
|  |  Revenue         Net Income       ICE Contracts     Legal Cases  |  |
|  |  $2.4B           $174M            $198M             47 active    |  |
|  |  ~~~~/\~~~~      ~~~~~~~/\        ~~~~/~~~~         +12 this Q   |  |
|  |  +8% YoY         +540% QoQ [!]   +22% YoY                       |  |
|  |                                                                  |  |
|  +------------------------------------------------------------------+  |
|                                                                        |
|  The [!] badge links to an auto-generated anomaly note:                |
|  "Q3 2025 net income of $174M is 6.4x the trailing average of $27M.   |
|   This may indicate new ICE contract awards or one-time events."       |
|                                                                        |
+------------------------------------------------------------------------+
|                                                                        |
|  +-- TABS: [Financials] [Contracts] [Legal Cases] [News] ---------+  |
|  |                                                                  |  |
|  |  FINANCIALS tab:                                                 |  |
|  |  Revenue & Net Income chart (dual-axis line chart, by quarter)   |  |
|  |  + table of recent 10-Q/10-K filings with links                 |  |
|  |                                                                  |  |
|  |  CONTRACTS tab:                                                  |  |
|  |  All USASpending awards where recipient = GEO Group              |  |
|  |  Timeline visualization of contract durations                    |  |
|  |                                                                  |  |
|  |  LEGAL tab:                                                      |  |
|  |  CourtListener cases mentioning GEO Group                        |  |
|  |                                                                  |  |
|  |  NEWS tab:                                                       |  |
|  |  GDELT events related to GEO Group facilities                    |  |
|  |                                                                  |  |
|  +------------------------------------------------------------------+  |
```

---

### Interaction Patterns

**Cross-Source Linking (the killer feature):**
Every entity card shows "Connected" chips linking to related records in other
data sources. This is powered by the entity resolution system. Clicking a
chip navigates to the linked record with context preserved.

```
Connected: [CoreCivic SEC Filing] [Contract HSCE-24-0012] [3 legal cases]
           ^blue chip              ^amber chip              ^blue chip
```

**Progressive Data Loading:**
- Skeleton screens on initial load (grey pulsing bars matching layout)
- Search results stream in as they arrive (vector results first, keyword merged in)
- Flight positions update every 10 seconds via WebSocket
- Charts animate data in on scroll-into-view

**Responsive Breakpoints:**
```
Desktop:  >= 1280px  (12-col grid, side-by-side panels)
Tablet:   >= 768px   (8-col, stacked panels, map still full-width)
Mobile:   < 768px    (single column, bottom sheet for flight details,
                      simplified charts, swipeable stat cards)
```

---

### Recommended Tech Stack (Frontend)

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Framework | Next.js 14 (App Router) | SSR for SEO, streaming for search results |
| Styling | Tailwind CSS | Rapid iteration, dark theme utilities |
| Charts | D3.js + Visx | Full control over data visualizations |
| Maps | Mapbox GL JS | Dark theme tiles, WebGL performance, animation |
| Tables | TanStack Table | Sorting, filtering, virtual scroll for large datasets |
| State | Zustand | Lightweight, works with SSR |
| API | tRPC or REST | Type-safe bridge to Python backend |
| Real-time | WebSocket (flights) | 10-second position updates |

---

### MVP Scope (Product Manager Recommendation)

**Phase 1 -- "Read-only transparency" (8 weeks)**
- Home dashboard with stat cards
- Contract explorer with filters and table
- Unified search across all sources
- Static flight list (no live map yet)
- About/methodology pages

**Phase 2 -- "Connect the dots" (6 weeks)**
- Cross-source entity linking in UI
- Corporate deep-dive pages
- Legal case browser
- Flight map with live positions

**Phase 3 -- "Power user tools" (6 weeks)**
- Saved searches and alerts
- Bulk data export (CSV, JSON)
- Public API with documentation
- Embeddable widgets for journalists

---

### Key Metrics to Track

| Metric | Target | Why |
|--------|--------|-----|
| Time to first meaningful search result | < 2s | Core UX quality |
| Cross-source link click-through rate | > 15% | Validates "connect the dots" value |
| Return visitor rate (7-day) | > 40% | Indicates research utility |
| Data export downloads / month | > 500 | Academic/journalist adoption |
| Search queries / session | > 3 | Indicates exploration depth |
