#!/usr/bin/env python3
"""
web_scraper.py - Simple web scraper built on requests + BeautifulSoup.

Fetch a URL, select elements via CSS selectors, and export the results as
JSON, CSV, or plain text.

Examples:
    # Extract all article titles from a blog
    python -m tools.web_scraper --url https://example.com --selector "h2.title"

    # Extract links and save as JSON
    python -m tools.web_scraper --url https://example.com --selector "a" --attr href \\
        --output links.json --format json

    # Set a custom User-Agent and timeout
    python -m tools.web_scraper --url https://example.com --selector "p" \\
        --user-agent "PyToolkit/1.0" --timeout 20
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

import requests
from bs4 import BeautifulSoup


DEFAULT_USER_AGENT = "PyToolkit-WebScraper/1.0 (+https://github.com/)"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="web-scraper",
        description="Scrape elements from a URL using CSS selectors.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  web-scraper --url https://example.com --selector 'h2.title'\n"
            "  web-scraper --url https://example.com --selector a --attr href -o links.json\n"
        ),
    )
    parser.add_argument("--url", "-u", required=True, help="URL to scrape.")
    parser.add_argument(
        "--selector", "-s", required=True,
        help="CSS selector, e.g. 'h2.title' or 'div.post > a'.",
    )
    parser.add_argument(
        "--attr", "-a",
        help="Extract a specific attribute (e.g., 'href', 'src'). Defaults to element text.",
    )
    parser.add_argument("--output", "-o", help="Output file path. If omitted, prints to stdout.")
    parser.add_argument(
        "--format", "-f",
        choices=["json", "csv", "text"], default="text",
        help="Output format (default: text).",
    )
    parser.add_argument("--timeout", type=float, default=10.0, help="Request timeout in seconds (default: 10).")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT, help="Custom User-Agent header.")
    parser.add_argument(
        "--limit", type=int,
        help="Maximum number of matches to return.",
    )
    parser.add_argument("--parser", default="html.parser", help="BeautifulSoup parser (default: html.parser).")
    return parser


def fetch_html(url: str, timeout: float, user_agent: str) -> str:
    """Fetch *url* and return the response body as text."""
    headers = {"User-Agent": user_agent}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def extract(html: str, selector: str, attr: str | None,
            parser: str, limit: int | None) -> List[Dict[str, Any]]:
    """Parse *html* and return a list of result dicts."""
    soup = BeautifulSoup(html, parser)
    elements = soup.select(selector)
    if limit is not None:
        elements = elements[:limit]

    results: List[Dict[str, Any]] = []
    for idx, el in enumerate(elements, start=1):
        if attr:
            value = el.get(attr, "")
        else:
            value = el.get_text(strip=True)
        results.append({
            "index": idx,
            "tag": el.name,
            "value": value,
        })
    return results


def render(results: List[Dict[str, Any]], fmt: str) -> str:
    """Render *results* into the chosen output format."""
    if fmt == "json":
        return json.dumps(results, indent=2, ensure_ascii=False)
    if fmt == "csv":
        if not results:
            return ""
        import io
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=["index", "tag", "value"])
        writer.writeheader()
        writer.writerows(results)
        return buffer.getvalue()
    # plain text
    return "\n".join(str(r["value"]) for r in results)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        html = fetch_html(args.url, args.timeout, args.user_agent)
    except requests.exceptions.Timeout:
        print(f"Error: request to {args.url} timed out after {args.timeout}s.", file=sys.stderr)
        return 1
    except requests.exceptions.HTTPError as exc:
        print(f"Error: HTTP error - {exc}", file=sys.stderr)
        return 1
    except requests.exceptions.RequestException as exc:
        print(f"Error: failed to fetch URL - {exc}", file=sys.stderr)
        return 1

    try:
        results = extract(html, args.selector, args.attr, args.parser, args.limit)
    except Exception as exc:  # BeautifulSoup raises assorted errors; surface them clearly.
        print(f"Error: failed to parse HTML - {exc}", file=sys.stderr)
        return 1

    output = render(results, args.format)

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
        print(f"Scraped {len(results)} element(s). Saved to {output_path}.")
    else:
        if output:
            print(output)
        print(f"\n[{len(results)} element(s) extracted]", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
