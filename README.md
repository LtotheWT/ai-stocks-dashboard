# AI Earnings Dashboard

Self-contained AI earnings dashboard for tracking US-listed AI-related companies and a separate broader watchlist.

For full context, data schema, source notes, and handoff details, see `HANDOFF.md`.

## Source of truth

- `companies.json` is the canonical data file.
- `index.html` embeds the same data in its inline `const data = { ... };` block.
- After changing `companies.json`, always sync the inline data block in `index.html`.

## Token-saving refresh workflow

For routine updates, manually run the merge helpers locally and ask Codex only to inspect errors, warnings, or final diffs.

### Prices

Prepare a prices JSON file, then run:

```bash
python3 .codex/skills/financial-advisor-price-refresh/scripts/merge_prices.py --repo . --prices-file /path/to/prices.json
```

Expected input shape:

```json
{
  "prices": {
    "AAPL": { "currentPrice": 280.10 },
    "MSFT": 410.81
  },
  "failures": []
}
```

### Earnings dates

Prepare an earnings-date updates JSON file, then run:

```bash
python3 .codex/skills/financial-advisor-earnings-date-refresh/scripts/merge_earnings_dates.py --repo . --updates-file /path/to/earnings_dates.json
```

Expected input shape:

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

## Quick validation

Run these after a manual merge:

```bash
python3 -c 'import json; json.load(open("companies.json")); print("companies.json OK")'
python3 .codex/skills/financial-advisor-earnings-date-refresh/scripts/merge_earnings_dates.py --repo . --audit-only
git diff --stat
```

Ask Codex to run the full workflow when sources conflict, a script fails, audit warnings are unclear, or a commit/PR review is needed.
