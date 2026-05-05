#!/usr/bin/env python3
"""Merge fetched prices into the financial_advisor dashboard files."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


def load_prices(path: Path) -> dict[str, float]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "prices" in raw:
        raw = raw["prices"]
    if not isinstance(raw, dict):
        raise SystemExit("prices file must contain a JSON object")

    prices: dict[str, float] = {}
    for ticker, value in raw.items():
        if ticker == "failures":
            continue
        if isinstance(value, dict):
            value = value.get("currentPrice")
        try:
            price = float(value)
        except (TypeError, ValueError):
            raise SystemExit(f"invalid price for {ticker}: {value!r}") from None
        if price <= 0:
            raise SystemExit(f"invalid non-positive price for {ticker}: {price}")
        prices[str(ticker).upper()] = round(price, 2)
    return prices


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
    sep = "\u00b7"
    subtitle = (
        f'{len(data.get("companies", []))} AI picks plus '
        f'{len(data.get("broaderWatchlist", []))} broader watchlist names '
        f'{sep} Last updated <span id="lastUpdated">{today}</span> {sep} Prices as of {today}'
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge currentPrice data into dashboard JSON and HTML.")
    parser.add_argument("--repo", default=".", help="Path to financial_advisor repo")
    parser.add_argument("--prices-file", required=True, help="JSON price map from fetch step")
    parser.add_argument("--date", default=date.today().isoformat(), help="YYYY-MM-DD date to write")
    parser.add_argument("--allow-partial", action="store_true", help="Allow missing dashboard tickers")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    companies_path = repo / "companies.json"
    index_path = repo / "index.html"
    prices = load_prices(Path(args.prices_file).expanduser().resolve())

    data = json.loads(companies_path.read_text(encoding="utf-8"))
    dashboard_tickers: list[str] = []
    seen: set[str] = set()
    changed: list[tuple[str, Any, float]] = []

    for section_name in ("companies", "broaderWatchlist"):
        for company in data.get(section_name, []):
            ticker = str(company.get("ticker", "")).upper()
            dashboard_tickers.append(ticker)
            if ticker not in prices:
                continue
            seen.add(ticker)
            old = company.get("currentPrice")
            new = prices[ticker]
            company["currentPrice"] = new
            if old != new:
                changed.append((ticker, old, new))

    missing_prices = sorted(set(dashboard_tickers) - set(prices))
    extra_prices = sorted(set(prices) - set(dashboard_tickers))
    if missing_prices and not args.allow_partial:
        raise SystemExit(f"missing prices for dashboard tickers: {', '.join(missing_prices)}")

    data["lastUpdated"] = args.date
    data["asOfPriceDate"] = args.date
    companies_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    html_lines = index_path.read_text(encoding="utf-8").splitlines(keepends=True)
    start, end = find_data_block(html_lines)
    html_lines[start : end + 1] = ["const data = " + json.dumps(data, indent=2, ensure_ascii=False) + ";\n"]
    html = update_subtitle("".join(html_lines), data, args.date)
    index_path.write_text(html, encoding="utf-8")

    print(f"updated_prices={len(seen)} changed={len(changed)} date={args.date}")
    if extra_prices:
        print(f"ignored extra tickers: {', '.join(extra_prices)}")
    for ticker, old, new in changed:
        print(f"{ticker}: {old} -> {new}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
