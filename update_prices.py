#!/usr/bin/env python3
"""
update_prices.py — Daily price refresh for AI Earnings Dashboard

Fetches live data for all tickers via yfinance, recalculates bull/bear
price bands, updates companies.json, then syncs the inline data block
in index.html.

Run manually:   python3 update_prices.py
Scheduled:      cron / launchd (see README or HANDOFF.md)

What gets updated automatically:
  currentPrice, trailingPE, trailingEPS, fwdPE, fwdEPS,
  marketCap, analystTarget, bullPrice, bearPrice,
  lastUpdated, asOfPriceDate

What still needs manual update (only changes at earnings):
  financials charts, health notes, thesis, keyRisks, dcf assumptions
"""

import json
import sys
from datetime import date
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("ERROR: yfinance not installed. Run: pip3 install yfinance --break-system-packages")
    sys.exit(1)

BASE_DIR = Path(__file__).parent
COMPANIES_FILE = BASE_DIR / "companies.json"
INDEX_FILE = BASE_DIR / "index.html"

# MU gets a larger bull P/E uplift (1.30) because memory is deeply cyclical
MU_TICKERS = {"MU"}


def format_market_cap(cap: float) -> str:
    if cap >= 1e12:
        return f"~${cap / 1e12:.1f}T"
    if cap >= 1e9:
        return f"~${cap / 1e9:.0f}B"
    return f"~${cap / 1e6:.0f}M"


def calc_bull_bear(ticker: str, fwd_pe: float, fwd_eps: float):
    bull_pe_mult = 1.30 if ticker in MU_TICKERS else 1.20
    bull = round((fwd_pe * bull_pe_mult) * (fwd_eps * 1.10), 2)
    bear = round((fwd_pe * 0.70) * (fwd_eps * 0.85), 2)
    return bull, bear


def apply_yf_info(company: dict, info: dict) -> dict:
    ticker = company["ticker"]
    changes = []

    price = info.get("currentPrice") or info.get("regularMarketPrice")
    if price:
        company["currentPrice"] = round(float(price), 2)
        changes.append(f"price=${price:.2f}")

    trailing_pe = info.get("trailingPE")
    if trailing_pe:
        company["trailingPE"] = round(float(trailing_pe), 2)

    fwd_pe = info.get("forwardPE")
    if fwd_pe:
        company["fwdPE"] = round(float(fwd_pe), 2)

    trailing_eps = info.get("trailingEps")
    if trailing_eps:
        company["trailingEPS"] = round(float(trailing_eps), 2)

    fwd_eps = info.get("forwardEps")
    if fwd_eps:
        company["fwdEPS"] = round(float(fwd_eps), 2)

    mkt_cap = info.get("marketCap")
    if mkt_cap:
        company["marketCap"] = format_market_cap(float(mkt_cap))

    target = info.get("targetMeanPrice")
    if target:
        company["analystTarget"] = round(float(target), 2)

    # Recalculate bull/bear using freshest fwdPE and fwdEPS we now have
    curr_fwd_pe = company.get("fwdPE")
    curr_fwd_eps = company.get("fwdEPS")
    if curr_fwd_pe and curr_fwd_eps and curr_fwd_pe > 0 and curr_fwd_eps > 0:
        bull, bear = calc_bull_bear(ticker, curr_fwd_pe, curr_fwd_eps)
        company["bullPrice"] = bull
        company["bearPrice"] = bear
        changes.append(f"bull=${bull} bear=${bear}")

    return company, changes


def sync_to_html(data: dict):
    html_lines = INDEX_FILE.read_text(encoding="utf-8").splitlines(keepends=True)

    start_idx = None
    end_idx = None
    for i, line in enumerate(html_lines):
        if line.strip().startswith("const data = {"):
            start_idx = i
        if start_idx is not None and i > start_idx and line.strip() == "};":
            end_idx = i
            break

    if start_idx is None or end_idx is None:
        print("WARNING: Could not locate 'const data = {...};' block in index.html — skipping sync.")
        return

    new_block = "const data = " + json.dumps(data, indent=2) + ";\n"
    html_lines[start_idx : end_idx + 1] = [new_block]
    INDEX_FILE.write_text("".join(html_lines), encoding="utf-8")
    print("Synced companies.json → index.html")


def main():
    data = json.loads(COMPANIES_FILE.read_text(encoding="utf-8"))

    all_sections = [
        ("companies", data.get("companies", [])),
        ("broaderWatchlist", data.get("broaderWatchlist", [])),
    ]

    tickers = [c["ticker"] for _, section in all_sections for c in section]
    print(f"Fetching {len(tickers)} tickers: {', '.join(tickers)}\n")

    yf_tickers = yf.Tickers(" ".join(tickers))

    ok = 0
    failed = []
    for section_name, section in all_sections:
        for i, company in enumerate(section):
            ticker = company["ticker"]
            try:
                info = yf_tickers.tickers[ticker].info
                updated, changes = apply_yf_info(company, info)
                section[i] = updated
                ok += 1
                print(f"  OK  {ticker:<6} {', '.join(changes) if changes else '(no changes)'}")
            except Exception as e:
                failed.append(ticker)
                print(f"  ERR {ticker:<6} {e}")

    today = date.today().isoformat()
    data["lastUpdated"] = today
    data["asOfPriceDate"] = today

    COMPANIES_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved companies.json  ({ok}/{len(tickers)} tickers updated, date={today})")
    if failed:
        print(f"Failed tickers (update manually): {', '.join(failed)}")

    sync_to_html(data)
    print("\nDone.")


if __name__ == "__main__":
    main()
