---
name: financial-advisor-company-add
description: Add, research, classify, or validate a new company/ticker for this financial_advisor AI Earnings Dashboard repo. Use when the user asks to add a company, decide whether it belongs in the AI earnings watchlist or broaderWatchlist, gather financial data for companies.json, scaffold a new ticker entry, or sync/validate a new dashboard company.
---

# Financial Advisor Company Add

## Scope

Use this skill from the `financial_advisor` repo root, where `companies.json` and `index.html` live.

`companies.json` is the source of truth. `index.html` is self-contained and must be synced after every JSON change by replacing its inline `const data = {...};` block and updating static counts/dates in the page header.

This skill is for adding a new ticker or materially rebuilding a company object. For price-only or earnings-date-only refreshes, use the existing repo skills:
- `$financial-advisor-price-refresh`
- `$financial-advisor-earnings-date-refresh`

## Classification Rules

Add to top-level `companies` when the stock thesis is directly tied to AI capex, AI infrastructure, or AI monetization:
- AI chips, custom silicon, HBM/memory, foundry, semiconductor equipment, test, packaging
- data center networking, optical, servers, storage, power, cooling, grid, colocation
- hyperscaler AI cloud, AI data platforms, enterprise AI software, AI cybersecurity, AI observability
- a non-pure-play where AI is a core driver of valuation, revenue growth, or capex cycle exposure

Add to `broaderWatchlist` when AI is secondary, speculative, or only one optionality layer:
- consumer, platform, mobility, gaming, fintech, China/SEA platform, turnaround, quality compounder
- the stock will mostly move on non-AI fundamentals even if it has an AI angle
- the user personally wants to monitor it but it does not belong with direct AI beneficiaries

For broader names:
- set `"watchlist": "broader"`
- set `"tagClass"` to one of the existing broader tag classes when useful: `quality`, `auto`, `platform`, `turnaround`, `other`
- phrase `thesis` and `macroAngle` as a broader watch angle, not an AI-pure-play thesis

If classification is borderline, state the reason and choose conservatively. The user prefers AI names kept separate from non-AI personal watchlist names.

## Research Workflow

Always verify current finance data with live sources before adding a company. Use direct source links in the final explanation when quoting figures.

Preferred source order:
1. Company IR page for earnings date/time and latest quarter.
2. StockAnalysis quote/statistics/forecast pages for price, market cap, P/E, EPS, analyst target, profitability.
3. StockAnalysis financials and cash-flow statement pages for annual income/cash-flow history.
4. Company 10-Q/10-K or earnings release for latest quarterly financials when StockAnalysis is stale.
5. Cross-check forward P/E/EPS with GuruFocus, Zacks, MarketBeat, TipRanks, or Yahoo Finance when the number looks strange.

Use annual and quarterly statement values in millions USD, matching existing `companies.json`.

## Required Company Object

A new entry should include:
- identity: `ticker`, `name`, `sector`, `subTheme`
- broader-only metadata: `watchlist`, `tagClass`
- event fields: `earningsDate`, `earningsTime`
- valuation snapshot: `currentPrice`, `fwdPE`, `trailingPE`, `fwdEPS`, `trailingEPS`, `marketCap`, `analystTarget`
- narrative fields: `thesis`, `macroAngle`, `expectedMove`, `keyRisks`
- health summary: `revenueGrowth`, `grossMargin`, `operatingMargin`, `fcf`, `balance`
- profitability: `fcfMargin`, `roe`, `roa`, `source`
- financials: annual `income`, annual `cashFlow`, latest `quarterlyIncome`, latest `quarterlyCashFlow`, `source`, `quarterlySource`, `quarterlyYear`
- DCF: `fit`, `fcfToEps`, `growth`, `discount`, `terminal`, `note`

Do not omit the `dcf` block. The dashboard hides the DCF panel for a company without it.

## Valuation Rules

For most names:

```text
bullPrice = (current fwd P/E x 1.20) x (consensus fwd EPS x 1.10)
bearPrice = (current fwd P/E x 0.70) x (consensus fwd EPS x 0.85)
```

For deep cyclicals, semis, or turnaround names, explain any manual deviation in the thesis or DCF note. Do not make a stock look cheap by forcing aggressive DCF assumptions.

DCF defaults:
- `fit`: `Good` for stable cash compounders, `Fair` for cyclical or platform names, `Weak` for unprofitable/highly speculative names
- `discount`: usually `0.085` to `0.12`; use higher rates for leverage, cyclicality, or execution risk
- `terminal`: usually `0.02` to `0.03`
- `growth`: conservative/base/bull long-run cash-flow assumptions, not a revenue forecast

## Insert And Sync

Prepare one candidate JSON file containing either the company object directly or:

```json
{
  "section": "companies",
  "company": {
    "ticker": "EXAMPLE"
  }
}
```

Then run:

```bash
python3 .codex/skills/financial-advisor-company-add/scripts/merge_company.py --repo . --company-file /path/to/company.json --section auto
```

Useful flags:
- `--dry-run`: validate and show placement without writing
- `--allow-update`: replace an existing ticker in its section
- `--preserve-bands`: keep supplied `bullPrice` and `bearPrice` instead of recalculating
- `--last-updated YYYY-MM-DD --as-of-price-date YYYY-MM-DD`: preserve exact source snapshot dates

The helper updates:
- `companies.json`
- inline `const data = {...};` in `index.html`
- header subtitle counts and dates
- AI filter `All (N)`
- AI and broader section counts

## Validation

After adding a company, run:

```bash
python3 -c 'import json; json.load(open("companies.json")); print("companies.json OK")'
python3 .codex/skills/financial-advisor-company-add/scripts/merge_company.py --repo . --validate-only
node -e 'const fs=require("fs"); const html=fs.readFileSync("index.html","utf8"); const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]); scripts.forEach(script=>new Function(script)); console.log(`script blocks OK: ${scripts.length}`);'
tidy -q -e index.html
git diff --stat
```

If network/DNS fails in the sandbox while fetching finance data, rerun the same important fetch command with `sandbox_permissions=require_escalated` and a concise justification.

## Output Style

Keep the final explanation plain and source-transparent:
- say whether the ticker went into AI or broader watchlist and why
- list any source gaps or fields that used estimates
- avoid buy/sell advice
- flag weak stocks directly when the data does not support a strong thesis
