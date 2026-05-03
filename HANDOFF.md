# AI Earnings Dashboard — Handoff Notes

**Owner:** Ryan (wengthai94@gmail.com) · **Last assistant session:** 2026-05-03 · **Switching to:** Codex

---

## Project goal

Track US-listed AI-related companies reporting earnings between **2026-05-03 and 2026-07-03**, plus a separate **Broader Watchlist** for non-AI-pure-play names the owner wants to monitor.

For each company, the dashboard shows:
- Current price, fwd P/E, fwd EPS, financial-health snapshot
- Conservative and high-risk bull price bands
- Earnings date + countdown
- Plain-language thesis, watch/macro angle, and key risks
- Annual financial charts: income trend, cash-flow trend, profitability rank
- DCF estimate panel as a sanity check, not a price target

> **This is research/educational. Not investment advice. Owner is not an expert — keep glossary tooltips and plain-language explanations whenever showing financial terms.**

---

## File structure

```
/Users/wengthailim/Workspace/financial_advisor/
├── HANDOFF.md
├── companies.json      ← canonical data: 17 AI companies + broaderWatchlist
├── index.html          ← self-contained HTML/CSS/JS dashboard
└── ai-earnings-dashboard-may-jul-2026.pdf
```

**Important pattern:** `companies.json` is the source of truth, but the dashboard is self-contained. After editing JSON, sync the inline `const data = { ... };` block in `index.html`.

---

## Current dashboard state

### AI Earnings Watchlist: 17 names

| Date | Ticker | Sector | Sub-theme |
|------|--------|--------|-----------|
| May 4 | PLTR | AI Software | Enterprise & Government AI |
| May 5 | AMD | AI Chips | Data Center GPUs |
| May 5 | ANET | AI Infrastructure | AI Networking |
| May 6 | ARM | AI Chips | Compute IP / Royalties |
| May 14 | AMAT | AI Chips | Semicap Equipment |
| May 20 | NVDA | AI Chips | AI Accelerator flagship |
| May 21 | MRVL | AI Chips | Custom AI Silicon + Optical |
| May 27 | SNOW | AI Infrastructure | AI Data Platform |
| May 28 | DELL | AI Infrastructure | AI Servers |
| May 28 | MDB | AI Infrastructure | AI Database (Vector) |
| Jun 4 | AVGO | AI Chips | Custom AI ASICs + Networking |
| Jun 9 | CRWD | AI Software | AI Cybersecurity |
| Jun 11 | ADBE | AI Software | AI Creative |
| Jun 16 | ORCL | AI Infrastructure | AI Cloud (OCI) |
| Jun 24 | MU | AI Chips | HBM / Memory |
| Jul 23 | INTC | AI Chips | Foundry + Gaudi Turnaround (next print, est.) |
| Jul 29 | MSFT | AI Software | AI Cloud + Copilot + Custom Silicon (next print, est.) |

### Broader Watchlist: 4 names

These are intentionally separated from the AI thesis.

| Ticker | Theme | Current note |
|--------|-------|--------------|
| AAPL | Quality + services cash flow | Clean DCF name, mature FCF, buybacks, services margin. |
| TSLA | EV margins + autonomy optionality | High-beta story; current earnings do not support valuation without future optionality. |
| GRAB | Southeast Asia super-app | Long path to profit. GAAP profitability is new/fragile and TTM FCF is still negative. DCF is not very useful yet because fwd EPS is only about `$0.09`. |
| U | Game engine + ad-tech turnaround | GAAP net income and operating income are still negative; FCF is positive. Treat as turnaround, not quality compounder. |

---

## Major dashboard features now implemented

- **Plain-language macro thesis:** explains AI capex, chip/HBM/power/networking shortages, and why earnings matter.
- **Search button/form:** searches both AI watchlist and broader watchlist.
- **Separate Broader Watchlist section:** AAPL, TSLA, GRAB, U shown below AI list with separate tags.
- **Annual Financials panel for every company:** income trend, cash-flow trend, and profitability rank.
- **Profitability rank:** only FCF margin %, ROE %, ROA %, per owner request.
- **DCF Estimate panel:** bear/base/bull values with assumptions. Use as sanity check only.
- **DCF display fix:** low-priced stocks now show cents (`$1.36`) instead of rounding to whole dollars (`$1`).
- **Chart color fix:** financial chart colors now match legends. Negative values show as muted striped bars, not red metric-color overrides.
- **Micron price fix:** MU current price corrected to match market snapshot around `$542.21`; related valuation inputs adjusted.

Validation last run:
- `tidy -q -e index.html`
- JS syntax check via `new Function(...)`
- Modal smoke checks for all names
- `companies.json` and inline `index.html` data sync check

---

## Data schema

Top-level:

```json
{
  "lastUpdated": "2026-05-03",
  "asOfPriceDate": "2026-05-01",
  "methodology": "P/E band formula",
  "companies": [],
  "broaderWatchlist": []
}
```

Each company object:

```json
{
  "ticker": "STRING",
  "name": "STRING",
  "sector": "STRING",
  "tagClass": "optional CSS tag class for broader names",
  "watchlist": "optional: broader",
  "subTheme": "STRING",
  "earningsDate": "YYYY-MM-DD",
  "earningsTime": "After close | Before open | Reported",
  "currentPrice": 0,
  "fwdPE": 0,
  "trailingPE": 0,
  "fwdEPS": 0,
  "trailingEPS": 0,
  "marketCap": "~$XB",
  "analystTarget": 0,
  "thesis": "plain-language reason",
  "macroAngle": "AI macro angle or broader watch angle",
  "health": {
    "revenueGrowth": "STRING",
    "grossMargin": "STRING",
    "operatingMargin": "STRING",
    "fcf": "STRING",
    "balance": "STRING"
  },
  "bullPrice": 0,
  "bearPrice": 0,
  "expectedMove": "STRING | null",
  "keyRisks": "STRING",
  "financials": {
    "income": [
      { "year": "2025", "revenue": 0, "netIncome": 0, "ebitda": 0 }
    ],
    "cashFlow": [
      { "year": "2025", "operatingCashFlow": 0, "freeCashFlow": 0, "netIncome": 0, "dividends": 0, "stockComp": 0 }
    ],
    "source": "StockAnalysis financials, annual values in millions USD"
  },
  "profitability": {
    "fcfMargin": 0,
    "roe": 0,
    "roa": 0,
    "source": "StockAnalysis statistics..."
  },
  "dcf": {
    "fit": "Good | Fair | Weak",
    "fcfToEps": 0.85,
    "growth": [0.04, 0.10, 0.16],
    "discount": 0.10,
    "terminal": 0.03,
    "note": "plain-language note on why DCF fits / doesn't fit this name"
  }
}
```

> The `dcf` object is **per-company**, embedded directly in `companies.json`. The dashboard reads it as `c.dcf` when rendering the DCF Estimate panel. There is no separate `dcfProfiles` lookup table — adding a ticker without a `dcf` block will silently hide the DCF panel for that name.

---

## Valuation methodology

### P/E scenario bands

For most names:

```
bullPrice = (current fwd P/E × 1.20) × (consensus fwd EPS × 1.10)
bearPrice = (current fwd P/E × 0.70) × (consensus fwd EPS × 0.85)
```

**Exception:** MU uses a larger bull multiple uplift (`1.30`) because memory is deeply cyclical and can re-rate harder.

### DCF panel

DCF is now present in the dashboard. Treat it as a **sanity check**, not a target. It is most useful for mature FCF names like AAPL, ADBE, AVGO, DELL, ORCL. It is weak for:
- GRAB: fwd EPS is tiny and TTM FCF is negative, so DCF prints low.
- TSLA: valuation depends on autonomy/robotaxi/robotics optionality.
- U: turnaround and GAAP losses make assumptions fragile.
- MU/AMAT/MRVL: cyclicality can make smooth DCF misleading.

Grab-specific note: the owner noticed the bull DCF looked like `$1`. It was actually about `$1.36`; the dashboard was rounding low-priced DCF values to whole dollars. That display bug is fixed. The deeper point remains: Grab needs durable FCF before DCF becomes a strong valuation tool.

---

## Refresh / edit workflow

1. Edit `companies.json` first.
2. Sync the inline `const data = { ... };` block in `index.html`.
3. If count changes, update:
   - Header subtitle
   - `All (15)` AI filter button if AI count changes
   - Broader section count if broader count changes
4. Validate:
   - `node -e "JSON.parse(require('fs').readFileSync('companies.json','utf8'))"`
   - `tidy -q -e index.html`
   - JS syntax check by extracting the `<script>` block and running `new Function(script)`
   - Modal smoke test for changed tickers

---

## Data sources and provenance

> The dashboard does not call a live finance API at runtime. Values in `companies.json` are manually captured snapshots, then copied into the inline `const data = { ... };` block in `index.html`. Treat prices, forward estimates, targets, and ratios as stale after a meaningful price move or a new earnings report.

Current snapshot dates:
- `lastUpdated`: `2026-05-03`
- `asOfPriceDate`: `2026-05-01`
- Financial statement charts: annual values in millions USD, mostly from StockAnalysis pages.
- Profitability ratios: current/TTM ratios, mostly from StockAnalysis statistics/ratios pages.

### Field-by-field source map

| Dashboard field | Primary source | Secondary/cross-check source | Notes |
|-----------------|----------------|------------------------------|-------|
| `earningsDate`, `earningsTime` | Company investor relations press releases | MarketBeat, TipRanks, Nasdaq earnings pages, Yahoo Finance calendar, Earnings Whispers / Wall Street Horizon | Prefer company IR when dates conflict. IR pages usually confirm date, time, and call link. |
| `currentPrice` | StockAnalysis quote page: `https://stockanalysis.com/stocks/{ticker}/` | CNBC, Investing.com, Yahoo Finance, Public.com | Price is a snapshot, not live. Update `asOfPriceDate` whenever refreshed. |
| `marketCap` | StockAnalysis quote/statistics pages | CompaniesMarketCap, CNBC, Yahoo Finance | If missing, derive from `currentPrice x shares outstanding`. |
| `fwdPE`, `trailingPE` | StockAnalysis statistics/metrics pages | GuruFocus, MacroTrends, finbox, Seeking Alpha | Forward P/E can differ by provider because forward EPS estimates differ. |
| `fwdEPS`, `trailingEPS` | StockAnalysis forecast/statistics pages, Zacks, MarketBeat, TipRanks | Company guidance, Seeking Alpha estimates | If forward EPS is not directly available, derive as `currentPrice / fwdPE` and label it as implied. |
| `analystTarget` | StockAnalysis forecast page | TipRanks, MarketBeat, Yahoo Finance analyst target | Use as a sanity check only; not a valuation target. |
| `health.revenueGrowth`, `grossMargin`, `operatingMargin`, `fcf`, `balance` | StockAnalysis financials/statistics pages | Company filings, earnings releases, 10-K/10-Q | These are plain-language summaries of the raw financial data. |
| Annual income chart: revenue, net income, EBITDA | StockAnalysis financials page: `https://stockanalysis.com/stocks/{ticker}/financials/` | Company 10-K/10-Q, Fiscal.ai/S&P Global data shown inside StockAnalysis | Values are in millions USD. |
| Annual cash-flow chart: operating cash flow, free cash flow, dividends, stock comp | StockAnalysis cash-flow page: `https://stockanalysis.com/stocks/{ticker}/financials/cash-flow-statement/` | Company 10-K/10-Q | Values are in millions USD. |
| Profitability rank: FCF margin, ROE, ROA | StockAnalysis statistics/ratios pages | Compute from financial statements if missing | Dashboard only shows these 3 ratios per owner request. |
| Thesis, macro angle, key risks | Company IR, filings, earnings-call commentary, and reputable market commentary | Manual analyst judgment from assistant | These are interpreted notes, not raw data. Keep them plain-language and cite sources when adding new claims. |
| Conservative / bull P/E bands | No external source | Computed from dashboard methodology | Formula lives in the "Valuation methodology" section above. |
| DCF estimate | No external source | Computed in `index.html` from per-company `dcf` assumptions, forward EPS, and `fcfToEps` proxy | Treat as a sanity check. It is weakest for GRAB, U, TSLA, and cyclical names. |

### Main source URLs

Use lowercase ticker in URL paths. Current tickers:
`pltr`, `amd`, `anet`, `arm`, `amat`, `nvda`, `mrvl`, `snow`, `dell`, `mdb`, `avgo`, `crwd`, `adbe`, `orcl`, `mu`, `aapl`, `tsla`, `grab`, `u`.

Updated AI watchlist tickers (lowercase): `pltr`, `amd`, `anet`, `arm`, `amat`, `nvda`, `mrvl`, `snow`, `dell`, `mdb`, `avgo`, `crwd`, `adbe`, `orcl`, `mu`, `msft`, `intc`. Broader watchlist: `aapl`, `tsla`, `grab`, `u`.

For each ticker, check these pages:
- Quote / overview: `https://stockanalysis.com/stocks/{ticker}/`
- Statistics: `https://stockanalysis.com/stocks/{ticker}/statistics/`
- Forecast / analyst target: `https://stockanalysis.com/stocks/{ticker}/forecast/`
- Income statement: `https://stockanalysis.com/stocks/{ticker}/financials/`
- Balance sheet: `https://stockanalysis.com/stocks/{ticker}/financials/balance-sheet/`
- Cash flow: `https://stockanalysis.com/stocks/{ticker}/financials/cash-flow-statement/`
- Ratios: `https://stockanalysis.com/stocks/{ticker}/financials/ratios/`

StockAnalysis source note:
- StockAnalysis publishes a provider breakdown at `https://stockanalysis.com/financial-sources/`.
- Their pages may show Fiscal.ai, S&P Global Market Intelligence, Nasdaq Data Link, or Financial Modeling Prep as the underlying financial data provider. Check the "Data Source" line at the bottom of each StockAnalysis page before citing.

Earnings/calendar backup pages:
- MarketBeat earnings page: `https://www.marketbeat.com/stocks/NASDAQ/{TICKER}/earnings/` or `https://www.marketbeat.com/stocks/NYSE/{TICKER}/earnings/`
- TipRanks earnings page: `https://www.tipranks.com/stocks/{ticker}/earnings`
- Nasdaq earnings page: `https://www.nasdaq.com/market-activity/stocks/{ticker}/earnings`
- Yahoo Finance earnings calendar: `https://finance.yahoo.com/calendar/earnings?symbol={TICKER}`

Forward estimate and valuation backup pages:
- Zacks earnings calendar: `https://www.zacks.com/stock/research/{TICKER}/earnings-calendar`
- GuruFocus forward P/E: `https://www.gurufocus.com/term/forward-pe-ratio/{TICKER}`
- MacroTrends historical valuation: `https://www.macrotrends.net/stocks/charts/{TICKER}/{slug}/pe-ratio`

### Data that is derived, not copied

- `bullPrice` and `bearPrice` are scenario outputs from the P/E formula, not source-page numbers.
- DCF bear/base/bull values are model outputs from dashboard assumptions, not analyst targets.
- If `fwdEPS` was not directly available, it may be implied from `currentPrice / fwdPE`.
- If `marketCap` was not directly available, it may be implied from `currentPrice x shares outstanding`.
- Dashboard text like "good fit", "weak fit", "turnaround", "fragile profit", and "sanity check" is assistant interpretation.

### Refresh workflow when sources update

When refreshing prices/EPS/dates for an existing ticker:
1. Hit the company IR page first for earnings date/time.
2. Pull StockAnalysis quote/statistics/forecast for price, P/E, EPS, market cap, and analyst target.
3. Pull StockAnalysis financials/cash-flow/ratios pages for annual charts and profitability.
4. Cross-check forward P/E and EPS against GuruFocus/Zacks/MarketBeat/TipRanks when the number looks strange.
5. Recompute `bullPrice`, `bearPrice`, and DCF outputs.
6. Update `lastUpdated` and `asOfPriceDate` in `companies.json`.
7. Sync `companies.json` into `index.html`.

### Citation hygiene

When quoting figures in the dashboard or in chat replies, include a markdown link to the source page. Owner explicitly asked for source transparency.

Recommended future schema improvement:

```json
"sources": {
  "quote": "https://stockanalysis.com/stocks/aapl/",
  "statistics": "https://stockanalysis.com/stocks/aapl/statistics/",
  "forecast": "https://stockanalysis.com/stocks/aapl/forecast/",
  "financials": "https://stockanalysis.com/stocks/aapl/financials/",
  "cashFlow": "https://stockanalysis.com/stocks/aapl/financials/cash-flow-statement/",
  "earnings": "company IR URL"
}
```

---

## Scheduled reminders

Reminders fire ~14 days before each AI earnings date, mostly from older Cowork scheduler state. They create Gmail drafts at wengthai94@gmail.com when available.

Known scheduled tasks from older handoff:
- earnings-reminder-pltr
- earnings-reminder-amd
- earnings-reminder-anet
- earnings-reminder-arm
- earnings-reminder-nvda
- earnings-reminder-amat
- earnings-reminder-snow
- earnings-reminder-mrvl
- earnings-reminder-dell
- earnings-reminder-mdb
- earnings-reminder-avgo
- earnings-reminder-crwd
- earnings-reminder-adbe
- earnings-reminder-orcl
- earnings-reminder-mu
- earnings-reminder-unity was previously disabled when Unity was removed from the AI watchlist. Unity is now back only as a broader watchlist name; do not assume an active reminder exists.

If using Codex without scheduled-task support, do not claim reminders were modified unless an automation tool confirms it.

---

## User preferences

- Wants normal-person readability, not heavy finance jargon.
- Likes direct pushback when a stock looks weak.
- Wants tooltips/glossary for financial terms.
- Wants research/scenarios, not buy/sell advice.
- Likes seeing current macro trend and what is scarce/crucial.
- Wants AI names kept separate from non-AI personal watchlist names.
- Interested in companies beyond AI, starting with AAPL, TSLA, GRAB, U.

---

## Open items / likely next asks

1. **Refresh after earnings reports.** Update actual revenue/EPS/guidance, forward estimates, valuation bands, DCF assumptions, and financial notes.
2. **Grab profitability follow-up.** Owner is skeptical that Grab has taken too long to become truly profitable. If asked, explain GAAP profit vs FCF vs subsidies plainly.
3. **Add more broader names.** Keep them in `broaderWatchlist`, not the AI list, unless the thesis is directly AI capex/monetization.
4. **Improve DCF model quality.** Current DCF uses EPS proxy. Better future version should use actual FCF/share where available, especially for companies with messy EPS/FCF differences.
5. **Visual QA.** After frontend changes, inspect the browser. Chart color/negative-value styling has been a prior issue.

---

## Safety lines

Do not:
- Give direct buy/sell instructions.
- Execute trades or move money.
- Treat DCF or P/E bands as predictions.
- Auto-send emails.

Do:
- Say “research/scenario,” “sanity check,” and “not investment advice.”
- Explain weak assumptions clearly.
- Call out when a model is unsuitable for a company.
