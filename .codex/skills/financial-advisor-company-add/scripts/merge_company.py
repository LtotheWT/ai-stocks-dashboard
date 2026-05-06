#!/usr/bin/env python3
"""Merge a prepared company object into the financial_advisor dashboard."""

from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any


VALID_SECTIONS = {"companies", "broaderWatchlist"}
BROADER_TAG_CLASSES = {"quality", "auto", "platform", "turnaround", "other"}

REQUIRED_FIELDS = [
    "ticker",
    "name",
    "sector",
    "subTheme",
    "earningsDate",
    "earningsTime",
    "currentPrice",
    "fwdPE",
    "trailingPE",
    "fwdEPS",
    "trailingEPS",
    "marketCap",
    "analystTarget",
    "thesis",
    "macroAngle",
    "health",
    "bullPrice",
    "bearPrice",
    "expectedMove",
    "keyRisks",
    "profitability",
    "financials",
    "dcf",
]

NUMERIC_FIELDS = [
    "currentPrice",
    "fwdPE",
    "trailingPE",
    "fwdEPS",
    "trailingEPS",
    "analystTarget",
    "bullPrice",
    "bearPrice",
]

HEALTH_FIELDS = ["revenueGrowth", "grossMargin", "operatingMargin", "fcf", "balance"]
PROFITABILITY_FIELDS = ["fcfMargin", "roe", "roa", "source"]
FINANCIALS_FIELDS = [
    "income",
    "cashFlow",
    "source",
    "quarterlyIncome",
    "quarterlyCashFlow",
    "quarterlySource",
    "quarterlyYear",
]
DCF_FIELDS = ["fit", "fcfToEps", "growth", "discount", "terminal", "note"]


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def normalize_ticker(company: dict[str, Any]) -> None:
    if "ticker" in company and isinstance(company["ticker"], str):
        company["ticker"] = company["ticker"].strip().upper()


def company_from_payload(payload: Any) -> tuple[dict[str, Any], str | None]:
    if not isinstance(payload, dict):
        raise SystemExit("company file must contain a JSON object")

    section = payload.get("section")
    company = payload.get("company", payload)
    if not isinstance(company, dict):
        raise SystemExit("company payload must be a JSON object")
    if section is not None and section not in VALID_SECTIONS:
        raise SystemExit(f"section must be one of: {', '.join(sorted(VALID_SECTIONS))}")

    company = deepcopy(company)
    normalize_ticker(company)
    return company, section


def infer_section(company: dict[str, Any], explicit_section: str | None, cli_section: str) -> str:
    if cli_section != "auto":
        return cli_section
    if explicit_section:
        return explicit_section
    if str(company.get("watchlist", "")).lower() == "broader":
        return "broaderWatchlist"
    return "companies"


def first_duplicate(data: dict[str, Any], ticker: str) -> tuple[str, int] | None:
    for section in VALID_SECTIONS:
        for idx, company in enumerate(data.get(section, [])):
            if str(company.get("ticker", "")).upper() == ticker:
                return section, idx
    return None


def calculate_bands(company: dict[str, Any]) -> tuple[float, float] | None:
    fwd_pe = company.get("fwdPE")
    fwd_eps = company.get("fwdEPS")
    if not isinstance(fwd_pe, (int, float)) or not isinstance(fwd_eps, (int, float)):
        return None
    if fwd_pe <= 0 or fwd_eps <= 0:
        return None

    bull_pe_multiplier = 1.3 if company.get("ticker") == "MU" else 1.2
    bull = (fwd_pe * bull_pe_multiplier) * (fwd_eps * 1.1)
    bear = (fwd_pe * 0.7) * (fwd_eps * 0.85)
    return round(bull, 2), round(bear, 2)


def apply_section_rules(company: dict[str, Any], section: str) -> None:
    if section == "broaderWatchlist":
        company["watchlist"] = "broader"
        company.setdefault("tagClass", "other")
    elif company.get("watchlist") == "broader":
        company.pop("watchlist", None)


def validate_company(
    company: dict[str, Any],
    section: str,
    *,
    require_quarterly: bool = True,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in company:
            errors.append(f"missing required field: {field}")

    ticker = company.get("ticker")
    if not isinstance(ticker, str) or not re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", ticker):
        errors.append("ticker must be an uppercase ticker-like string")

    earnings_date = company.get("earningsDate")
    if not isinstance(earnings_date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", earnings_date):
        errors.append("earningsDate must use YYYY-MM-DD")

    for field in NUMERIC_FIELDS:
        value = company.get(field)
        if value is not None and not isinstance(value, (int, float)):
            errors.append(f"{field} must be numeric")

    health = company.get("health")
    if isinstance(health, dict):
        for field in HEALTH_FIELDS:
            if field not in health:
                errors.append(f"health missing field: {field}")
    elif "health" in company:
        errors.append("health must be an object")

    profitability = company.get("profitability")
    if isinstance(profitability, dict):
        for field in PROFITABILITY_FIELDS:
            if field not in profitability:
                errors.append(f"profitability missing field: {field}")
    elif "profitability" in company:
        errors.append("profitability must be an object")

    financials = company.get("financials")
    if isinstance(financials, dict):
        for field in FINANCIALS_FIELDS:
            if field not in financials:
                if require_quarterly or not field.startswith("quarterly"):
                    errors.append(f"financials missing field: {field}")
                else:
                    warnings.append(f"financials missing field: {field}")
        for field in ["income", "cashFlow", "quarterlyIncome", "quarterlyCashFlow"]:
            value = financials.get(field)
            if value is not None and not isinstance(value, list):
                errors.append(f"financials.{field} must be a list")
    elif "financials" in company:
        errors.append("financials must be an object")

    dcf = company.get("dcf")
    if isinstance(dcf, dict):
        for field in DCF_FIELDS:
            if field not in dcf:
                errors.append(f"dcf missing field: {field}")
        growth = dcf.get("growth")
        if growth is not None and (not isinstance(growth, list) or len(growth) != 3):
            errors.append("dcf.growth must be a three-value list")
    elif "dcf" in company:
        errors.append("dcf must be an object")

    if section == "broaderWatchlist":
        if company.get("watchlist") != "broader":
            errors.append('broaderWatchlist entries must set watchlist to "broader"')
        tag_class = company.get("tagClass")
        if tag_class not in BROADER_TAG_CLASSES:
            warnings.append(
                "broaderWatchlist tagClass should usually be one of: "
                + ", ".join(sorted(BROADER_TAG_CLASSES))
            )
    elif company.get("watchlist") == "broader":
        errors.append('AI companies entries should not set watchlist to "broader"')

    if not company.get("dcf"):
        warnings.append("missing dcf will hide the DCF panel")

    return errors, warnings


def find_data_block(lines: list[str]) -> tuple[int, int]:
    start = end = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("const data = {"):
            start = idx
        elif start is not None and idx > start and line.strip() == "};":
            end = idx
            break
    if start is None or end is None:
        raise SystemExit("could not locate const data block in index.html")
    return start, end


def replace_once(pattern: str, repl: str, text: str, label: str, flags: int = 0) -> str:
    new_text, count = re.subn(pattern, repl, text, count=1, flags=flags)
    if count != 1:
        raise SystemExit(f"could not update {label} in index.html")
    return new_text


def sync_to_html(repo: Path, data: dict[str, Any]) -> None:
    index_path = repo / "index.html"
    lines = index_path.read_text(encoding="utf-8").splitlines(keepends=True)
    start, end = find_data_block(lines)
    lines[start : end + 1] = ["const data = " + json.dumps(data, indent=2, ensure_ascii=False) + ";\n"]
    html = "".join(lines)

    ai_count = len(data.get("companies", []))
    broader_count = len(data.get("broaderWatchlist", []))
    last_updated = data.get("lastUpdated", "")
    price_date = data.get("asOfPriceDate", "")
    bullet = "\u00b7"

    header = (
        f'<div class="sub">{ai_count} AI picks plus {broader_count} broader watchlist names '
        f'{bullet} Last updated <span id="lastUpdated">{last_updated}</span> '
        f'{bullet} Prices as of {price_date}</div>'
    )
    html = replace_once(r'<div class="sub">.*?</div>', header, html, "header subtitle")
    html = replace_once(
        r'(<button class="filter-btn active" data-filter="all">All \()\d+(\)</button>)',
        rf"\g<1>{ai_count}\g<2>",
        html,
        "AI filter count",
    )
    html = replace_once(
        r'(<h2>AI Earnings Watchlist</h2>.*?<span class="section-count">)\d+ names(</span>)',
        rf"\g<1>{ai_count} names\g<2>",
        html,
        "AI section count",
        flags=re.S,
    )
    html = replace_once(
        r'(<h2>Broader Watchlist</h2>.*?<span class="section-count">)\d+ names(</span>)',
        rf"\g<1>{broader_count} names\g<2>",
        html,
        "broader section count",
        flags=re.S,
    )

    index_path.write_text(html, encoding="utf-8")


def validate_dashboard(repo: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    missing_quarterly: dict[str, list[str]] = {}
    companies_path = repo / "companies.json"
    index_path = repo / "index.html"

    data = load_json(companies_path)
    if not isinstance(data, dict):
        return ["companies.json top-level value must be an object"], warnings

    seen: set[str] = set()
    for section in ["companies", "broaderWatchlist"]:
        entries = data.get(section)
        if not isinstance(entries, list):
            errors.append(f"{section} must be a list")
            continue
        for company in entries:
            if not isinstance(company, dict):
                errors.append(f"{section} contains a non-object entry")
                continue
            ticker = str(company.get("ticker", "")).upper()
            if ticker in seen:
                errors.append(f"duplicate ticker: {ticker}")
            seen.add(ticker)
            company_errors, company_warnings = validate_company(company, section, require_quarterly=False)
            errors.extend(f"{ticker}: {message}" for message in company_errors)
            for message in company_warnings:
                prefix = "financials missing field: "
                if message.startswith(prefix) and message[len(prefix) :].startswith("quarterly"):
                    missing_quarterly.setdefault(ticker, []).append(message[len(prefix) :])
                else:
                    warnings.append(f"{ticker}: {message}")

    if missing_quarterly:
        tickers = ", ".join(sorted(missing_quarterly))
        warnings.append(
            f"{len(missing_quarterly)} existing companies missing quarterly financial fields: {tickers}"
        )

    if index_path.exists():
        lines = index_path.read_text(encoding="utf-8").splitlines(keepends=True)
        start, end = find_data_block(lines)
        block = "".join(lines[start : end + 1]).strip()
        prefix = "const data = "
        if not block.startswith(prefix) or not block.endswith(";"):
            errors.append("index.html data block has unexpected format")
        else:
            inline_data = json.loads(block[len(prefix) : -1])
            if inline_data != data:
                errors.append("index.html inline data does not match companies.json")

    return errors, warnings


def merge_company(args: argparse.Namespace) -> None:
    repo = Path(args.repo).resolve()
    data_path = repo / "companies.json"
    data = load_json(data_path)
    payload = load_json(Path(args.company_file))
    company, payload_section = company_from_payload(payload)
    section = infer_section(company, payload_section, args.section)

    apply_section_rules(company, section)
    if not args.preserve_bands:
        bands = calculate_bands(company)
        if bands:
            company["bullPrice"], company["bearPrice"] = bands

    errors, warnings = validate_company(company, section)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)

    ticker = company["ticker"]
    duplicate = first_duplicate(data, ticker)
    action = "insert"
    target_index = None
    if duplicate:
        duplicate_section, duplicate_index = duplicate
        if not args.allow_update:
            raise SystemExit(f"{ticker} already exists in {duplicate_section}; pass --allow-update to replace it")
        section = duplicate_section
        target_index = duplicate_index
        apply_section_rules(company, section)
        action = "update"

    today = date.today().isoformat()
    data["lastUpdated"] = args.last_updated or today
    data["asOfPriceDate"] = args.as_of_price_date or today

    if action == "update" and target_index is not None:
        data[section][target_index] = company
    else:
        data.setdefault(section, []).append(company)

    print(f"{action}: {ticker} -> {section}")
    for warning in warnings:
        print(f"WARNING: {warning}")

    if args.dry_run:
        print("dry run: no files written")
        return

    dump_json(data_path, data)
    if not args.no_sync:
        sync_to_html(repo, data)
        print("synced index.html")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repo root containing companies.json and index.html")
    parser.add_argument("--company-file", help="Prepared JSON company object or {section, company} payload")
    parser.add_argument(
        "--section",
        default="auto",
        choices=["auto", "companies", "broaderWatchlist"],
        help="Target section. auto uses payload section or watchlist=broader.",
    )
    parser.add_argument("--allow-update", action="store_true", help="Replace an existing ticker")
    parser.add_argument("--preserve-bands", action="store_true", help="Keep supplied bullPrice/bearPrice")
    parser.add_argument("--last-updated", help="Top-level lastUpdated date")
    parser.add_argument("--as-of-price-date", help="Top-level asOfPriceDate")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print placement without writing")
    parser.add_argument("--no-sync", action="store_true", help="Do not sync companies.json into index.html")
    parser.add_argument("--validate-only", action="store_true", help="Validate companies.json and index.html sync")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if args.validate_only:
        errors, warnings = validate_dashboard(repo)
        for warning in warnings:
            print(f"WARNING: {warning}")
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            raise SystemExit(1)
        print("dashboard company data OK")
        return

    if not args.company_file:
        parser.error("--company-file is required unless --validate-only is used")

    merge_company(args)


if __name__ == "__main__":
    main()
