#!/usr/bin/env python3
"""Merge earnings dates into the financial_advisor dashboard files, or audit stale dates."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any


TIME_ALIASES = {
    "bmo": "Before open",
    "before market open": "Before market open",
    "before open": "Before open",
    "amc": "After close",
    "after market close": "After close",
    "after close": "After close",
    "reported": "Reported",
}


def parse_iso_date(value: Any, ticker: str) -> str:
    text = str(value or "").strip()
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        raise SystemExit(f"invalid earningsDate for {ticker}: {value!r}") from None
    return text


def normalize_time(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return text
    estimated = "(est" in text.lower()
    key = text.lower().replace("(est.)", "").replace("(est)", "").strip()
    normalized = TIME_ALIASES.get(key, text)
    if estimated and "est" not in normalized.lower() and normalized != "Reported":
        normalized = f"{normalized} (est.)"
    return normalized


def load_updates(path: Path) -> dict[str, dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "updates" in raw:
        raw = raw["updates"]
    if not isinstance(raw, dict):
        raise SystemExit("updates file must contain a JSON object")

    updates: dict[str, dict[str, Any]] = {}
    for ticker, value in raw.items():
        if ticker == "failures":
            continue
        if not isinstance(value, dict):
            raise SystemExit(f"invalid update for {ticker}: expected object")
        date_value = value.get("earningsDate", value.get("reportDate"))
        time_value = value.get("earningsTime", value.get("reportTime", value.get("time")))
        updates[str(ticker).upper()] = {
            "earningsDate": parse_iso_date(date_value, str(ticker).upper()),
            "earningsTime": normalize_time(time_value),
        }
    return updates


def dashboard_companies(data: dict[str, Any]) -> list[dict[str, Any]]:
    return list(data.get("companies", [])) + list(data.get("broaderWatchlist", []))


def find_data_block(lines: list[str]) -> tuple[int, int]:
    start = end = None
    for i, line in enumerate(lines):
        if line.strip().startswith("const data = {"):
            start = i
        elif start is not None and i > start and line.strip() == "};":
            end = i
            break
    if start is None or end is None:
        raise SystemExit("Could not locate inline const data block in index.html")
    return start, end


def update_subtitle(html: str, data: dict[str, Any], today: str) -> str:
    price_date = data.get("asOfPriceDate", today)
    sep = "\u00b7"
    subtitle = (
        f'{len(data.get("companies", []))} AI picks plus '
        f'{len(data.get("broaderWatchlist", []))} broader watchlist names '
        f'{sep} Last updated <span id="lastUpdated">{today}</span> {sep} Prices as of {price_date}'
    )
    pattern = (
        r'<div class="sub">[^<]*AI picks plus [^<]*broader watchlist names '
        r'(?:\u00b7|-) Last updated <span id="lastUpdated">[^<]*</span> '
        r'(?:\u00b7|-) Prices as of [^<]*</div>'
    )
    html, replacements = re.subn(pattern, f'<div class="sub">{subtitle}</div>', html, count=1)
    if replacements != 1:
        raise SystemExit("Could not update dashboard subtitle")
    return html


def audit(data: dict[str, Any], html: str, effective_date: str) -> int:
    warnings = 0
    today = datetime.strptime(effective_date, "%Y-%m-%d").date()
    hardcoded_today = re.search(r"const\s+today\s*=\s*new Date\('(\d{4}-\d{2}-\d{2})'\)", html)
    if hardcoded_today and hardcoded_today.group(1) != effective_date:
        warnings += 1
        print(f"WARN hardcoded today is {hardcoded_today.group(1)}, expected {effective_date}")

    for company in dashboard_companies(data):
        ticker = company.get("ticker", "?")
        earnings_date = parse_iso_date(company.get("earningsDate"), ticker)
        report_day = datetime.strptime(earnings_date, "%Y-%m-%d").date()
        earnings_time = str(company.get("earningsTime", ""))
        if report_day < today and "reported" not in earnings_time.lower():
            warnings += 1
            print(f"WARN {ticker}: past earningsDate {earnings_date} still has earningsTime={earnings_time!r}")
    print(f"audit_warnings={warnings}")
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge or audit earningsDate/earningsTime data.")
    parser.add_argument("--repo", default=".", help="Path to financial_advisor repo")
    parser.add_argument("--updates-file", help="JSON earnings date update map")
    parser.add_argument("--date", default=date.today().isoformat(), help="YYYY-MM-DD effective dashboard date")
    parser.add_argument("--allow-partial", action="store_true", help="Allow missing dashboard tickers")
    parser.add_argument("--audit-only", action="store_true", help="Only audit current dashboard dates")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    companies_path = repo / "companies.json"
    index_path = repo / "index.html"
    data = json.loads(companies_path.read_text(encoding="utf-8"))
    html = index_path.read_text(encoding="utf-8")

    if args.audit_only:
        return 0 if audit(data, html, args.date) == 0 else 1

    if not args.updates_file:
        raise SystemExit("--updates-file is required unless --audit-only is used")

    updates = load_updates(Path(args.updates_file).expanduser().resolve())
    dashboard_tickers = [str(company.get("ticker", "")).upper() for company in dashboard_companies(data)]
    missing_updates = sorted(set(dashboard_tickers) - set(updates))
    extra_updates = sorted(set(updates) - set(dashboard_tickers))
    if missing_updates and not args.allow_partial:
        raise SystemExit(f"missing updates for dashboard tickers: {', '.join(missing_updates)}")

    changed: list[tuple[str, str, str, str, str]] = []
    for section_name in ("companies", "broaderWatchlist"):
        for company in data.get(section_name, []):
            ticker = str(company.get("ticker", "")).upper()
            if ticker not in updates:
                continue
            update = updates[ticker]
            old_date = company.get("earningsDate")
            old_time = company.get("earningsTime")
            company["earningsDate"] = update["earningsDate"]
            company["earningsTime"] = update["earningsTime"]
            if old_date != company["earningsDate"] or old_time != company["earningsTime"]:
                changed.append((ticker, old_date, old_time, company["earningsDate"], company["earningsTime"]))

    data["lastUpdated"] = args.date
    companies_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    html_lines = html.splitlines(keepends=True)
    start, end = find_data_block(html_lines)
    html_lines[start : end + 1] = ["const data = " + json.dumps(data, indent=2, ensure_ascii=False) + ";\n"]
    html = update_subtitle("".join(html_lines), data, args.date)
    index_path.write_text(html, encoding="utf-8")

    print(f"updated_earnings_dates={len(updates) - len(extra_updates)} changed={len(changed)} date={args.date}")
    if extra_updates:
        print(f"ignored extra tickers: {', '.join(extra_updates)}")
    for ticker, old_date, old_time, new_date, new_time in changed:
        print(f"{ticker}: {old_date} {old_time} -> {new_date} {new_time}")
    audit(data, html, args.date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
