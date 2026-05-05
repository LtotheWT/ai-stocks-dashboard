---
name: financial-advisor-earnings-date-refresh
description: Refresh earnings/report dates for this financial_advisor AI Earnings Dashboard repo. Use when the user asks to update, verify, or audit earningsDate, earningsTime, report dates, financial report dates, stale Today/Reported badges, or upcoming earnings countdowns in a repo with companies.json and a self-contained index.html dashboard. Also use when the user asks to run this workflow with parallel agents.
---

# Financial Advisor Earnings Date Refresh

## Scope

Use this skill from the `financial_advisor` repo root, where `companies.json` and `index.html` live.

`companies.json` is the source of truth. `index.html` is self-contained and must be synced after every JSON change by replacing its inline `const data = {...};` block.

For an earnings-date-only request, update only:
- each company object's `earningsDate`
- each company object's `earningsTime`
- top-level `lastUpdated`
- the header subtitle's `Last updated` date

Do not update `currentPrice`, `asOfPriceDate`, valuation fields, thesis text, financial statements, or DCF assumptions unless the user explicitly asks for a broader refresh.

## Data Rules

- Use ISO dates: `YYYY-MM-DD`.
- Use consistent times: `Before open`, `Before market open`, `After close`, `After close (est.)`, `Before open (est.)`, or `Reported`.
- Prefer confirmed company IR/exchange/calendar sources over estimates.
- Preserve `(est.)` when the source is estimated or not company-confirmed.
- For dates before the effective dashboard date, either set `earningsTime` to `Reported` or flag the ticker for manual review.
- Do not silently overwrite manually curated notes or source text.

## Workflow

1. Confirm the repo state:
   - `git status --short`
   - `jq -r '"companies=" + (.companies|length|tostring) + " broaderWatchlist=" + (.broaderWatchlist|length|tostring)' companies.json`
   - `jq -r '([.companies[].ticker] + [.broaderWatchlist[].ticker]) | join(" ")' companies.json`

2. Audit the current dashboard before fetching:
   - `python3 .codex/skills/financial-advisor-earnings-date-refresh/scripts/merge_earnings_dates.py --repo . --audit-only`
   - Check for hardcoded date/countdown logic in `index.html`; stale `Today` badges are often caused by a hardcoded `const today = new Date('YYYY-MM-DD')`.

3. Fetch or verify dates for all tickers from both `companies` and `broaderWatchlist`.

4. If the user explicitly asks for parallel agents, split tickers into disjoint batches and spawn agents. Tell agents:
   - fetch earnings/report date and report timing only
   - do not edit files
   - return compact JSON mapping ticker to `earningsDate`, `earningsTime`, `source`, and `confirmed`
   - flag uncertain dates instead of guessing

5. If network/DNS fails in the sandbox, rerun the same important fetch command with `sandbox_permissions=require_escalated` and a concise justification. Do not ask in prose before requesting approval.

6. Merge date results once, from the parent agent, to avoid conflicting file writes. Prefer the repo-local helper script:
   - `python3 .codex/skills/financial-advisor-earnings-date-refresh/scripts/merge_earnings_dates.py --repo . --updates-file /path/to/earnings_dates.json`

7. Validate:
   - `python3 -c 'import json; json.load(open("companies.json")); print("companies.json OK")'`
   - inline `index.html` data equals `companies.json`
   - JavaScript syntax check with `new Function(...)`
   - `tidy -q -e index.html`
   - rerun the audit helper and review stale past-date warnings
   - `git diff --stat`

## Update JSON Format

The helper accepts either shape:

```json
{
  "updates": {
    "PLTR": {
      "earningsDate": "2026-05-04",
      "earningsTime": "Reported",
      "source": "Company IR",
      "confirmed": true
    }
  },
  "failures": []
}
```

or:

```json
{
  "PLTR": {
    "earningsDate": "2026-05-04",
    "earningsTime": "Reported"
  }
}
```

The helper requires every dashboard ticker to be present by default. Use `--allow-partial` only when intentionally updating a subset.

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
