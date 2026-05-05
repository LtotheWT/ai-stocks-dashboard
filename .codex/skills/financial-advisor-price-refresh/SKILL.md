---
name: financial-advisor-price-refresh
description: Refresh share prices for this financial_advisor AI Earnings Dashboard repo. Use when the user asks to update, refresh, or verify company share prices, stock prices, currentPrice fields, or price dates in a repo that contains companies.json and a self-contained index.html dashboard. Also use when the user asks to run this workflow with parallel agents.
---

# Financial Advisor Price Refresh

## Scope

Use this skill from the `financial_advisor` repo root, where `companies.json` and `index.html` live.

`companies.json` is the source of truth. `index.html` is self-contained and must be synced after every JSON change by replacing its inline `const data = {...};` block.

For a share-price-only request, update only:
- each company object's `currentPrice`
- top-level `lastUpdated`
- top-level `asOfPriceDate`
- the header subtitle dates in `index.html`

Do not update `fwdPE`, `trailingPE`, `fwdEPS`, `trailingEPS`, `marketCap`, `analystTarget`, financial statements, thesis text, or DCF assumptions unless the user explicitly asks for a broader valuation refresh.

## Workflow

1. Confirm the repo state:
   - `git status --short`
   - `jq -r '"companies=" + (.companies|length|tostring) + " broaderWatchlist=" + (.broaderWatchlist|length|tostring)' companies.json`
   - `jq -r '([.companies[].ticker] + [.broaderWatchlist[].ticker]) | join(" ")' companies.json`

2. Fetch all tickers from both `companies` and `broaderWatchlist`.

3. If the user explicitly asks for parallel agents, split tickers into disjoint batches and spawn agents. Tell agents:
   - fetch prices only
   - do not edit files
   - return compact JSON mapping ticker to `currentPrice`, plus failures
   - use Yahoo Finance via `yfinance` when available

4. If the user does not explicitly ask for agents, fetch prices locally. When present, the existing cached dependency path can be used with:
   - `PYTHONPATH=/private/tmp/financial_advisor_deps python3 ...`

5. If network/DNS fails in the sandbox, rerun the same important fetch command with `sandbox_permissions=require_escalated` and a concise justification. Do not ask in prose before requesting approval.

6. Merge price results once, from the parent agent, to avoid conflicting file writes. Prefer the repo-local helper script:
   - `python3 .codex/skills/financial-advisor-price-refresh/scripts/merge_prices.py --repo . --prices-file /path/to/prices.json`

7. Validate:
   - `python3 -c 'import json; json.load(open("companies.json")); print("companies.json OK")'`
   - inline `index.html` data equals `companies.json`
   - JavaScript syntax check with `new Function(...)`
   - `tidy -q -e index.html`
   - `git diff --stat`

## Price JSON Format

The helper accepts either shape:

```json
{
  "prices": {
    "AAPL": { "currentPrice": 280.109985 },
    "MSFT": 410.81
  },
  "failures": []
}
```

or:

```json
{
  "AAPL": { "currentPrice": 280.109985 },
  "MSFT": 410.81
}
```

The helper rounds prices to two decimals, requires every ticker in the dashboard to be present by default, updates both files, and prints changed tickers.

## Validation Snippets

Inline data sync check:

```bash
python3 - <<'PY'
import json
from pathlib import Path
lines = Path('index.html').read_text(encoding='utf-8').splitlines()
start = end = None
for i, line in enumerate(lines):
    if line.strip().startswith('const data = {'):
        start = i
    elif start is not None and i > start and line.strip() == '};':
        end = i
        break
if start is None or end is None:
    raise SystemExit('data block not found')
block = '\n'.join(lines[start:end + 1])
inline = json.loads(block[len('const data = '):-1])
canonical = json.loads(Path('companies.json').read_text(encoding='utf-8'))
if inline != canonical:
    raise SystemExit('inline data sync FAILED')
print('inline data sync OK')
PY
```

JavaScript syntax check:

```bash
node -e 'const fs=require("fs"); const html=fs.readFileSync("index.html","utf8"); const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]); scripts.forEach(script=>new Function(script)); console.log(`script blocks OK: ${scripts.length}`);'
```
