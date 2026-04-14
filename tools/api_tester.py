#!/usr/bin/env python3
"""
api_tester.py - REST API testing tool.

Issue HTTP requests of any method with custom headers, query params, and body.
Shows status code, response headers, body, and elapsed time.

Examples:
    # Simple GET
    python -m tools.api_tester --url https://api.github.com/users/octocat

    # POST with JSON body
    python -m tools.api_tester --url https://httpbin.org/post --method POST \\
        --json '{"name": "Alperen"}' --header "X-Api-Key: secret"

    # Read body from file and save response
    python -m tools.api_tester --url https://httpbin.org/put --method PUT \\
        --data-file payload.json --save response.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

import requests


HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="api-tester",
        description="Send HTTP requests and inspect responses.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  api-tester -u https://api.github.com/users/octocat\n"
            "  api-tester -u https://httpbin.org/post -X POST --json '{\"k\":\"v\"}'\n"
            "  api-tester -u https://httpbin.org/get -H 'X-Api-Key: secret' -q foo=bar\n"
        ),
    )
    parser.add_argument("--url", "-u", required=True, help="Request URL.")
    parser.add_argument(
        "--method", "-X", choices=HTTP_METHODS, default="GET",
        help="HTTP method (default: GET).",
    )
    parser.add_argument(
        "--header", "-H", action="append", default=[],
        help="Custom header in 'Key: Value' form. Repeatable.",
    )
    parser.add_argument(
        "--query", "-q", action="append", default=[],
        help="Query parameter in 'key=value' form. Repeatable.",
    )

    body_group = parser.add_mutually_exclusive_group()
    body_group.add_argument("--data", "-d", help="Raw request body string.")
    body_group.add_argument("--json", dest="json_body", help="JSON request body string.")
    body_group.add_argument("--data-file", help="Read request body from a file.")

    parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout seconds (default: 30).")
    parser.add_argument("--no-verify", action="store_true", help="Disable TLS certificate verification.")
    parser.add_argument("--save", help="Save response body to this file.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print request details before sending.")
    return parser


def parse_headers(pairs: list[str]) -> Dict[str, str]:
    """Parse ``['Key: Value', ...]`` into a dict."""
    headers: Dict[str, str] = {}
    for raw in pairs:
        if ":" not in raw:
            raise ValueError(f"Invalid header '{raw}'. Expected 'Key: Value'.")
        key, _, value = raw.partition(":")
        headers[key.strip()] = value.strip()
    return headers


def parse_queries(pairs: list[str]) -> Dict[str, str]:
    """Parse ``['key=value', ...]`` into a dict."""
    params: Dict[str, str] = {}
    for raw in pairs:
        if "=" not in raw:
            raise ValueError(f"Invalid query '{raw}'. Expected 'key=value'.")
        key, _, value = raw.partition("=")
        params[key.strip()] = value.strip()
    return params


def load_body(args: argparse.Namespace) -> tuple[Optional[str], Optional[Any]]:
    """Return (raw_data, json_body). Exactly one - or neither - is set."""
    if args.json_body is not None:
        try:
            return None, json.loads(args.json_body)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid --json value: {exc}") from exc
    if args.data_file is not None:
        path = Path(args.data_file).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f"Data file '{path}' not found.")
        content = path.read_text(encoding="utf-8")
        # If file looks like JSON, send as JSON; otherwise send as raw text.
        if path.suffix.lower() == ".json":
            try:
                return None, json.loads(content)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in '{path}': {exc}") from exc
        return content, None
    if args.data is not None:
        return args.data, None
    return None, None


def format_response(response: requests.Response, elapsed_ms: float) -> str:
    """Build a human-readable response summary."""
    lines = [
        f"Status:   {response.status_code} {response.reason}",
        f"Elapsed:  {elapsed_ms:.1f} ms",
        f"Size:     {len(response.content)} bytes",
        "",
        "Headers:",
    ]
    for key, value in response.headers.items():
        lines.append(f"  {key}: {value}")
    lines.append("")
    lines.append("Body:")
    content_type = response.headers.get("Content-Type", "")
    if "application/json" in content_type:
        try:
            lines.append(json.dumps(response.json(), indent=2, ensure_ascii=False))
        except ValueError:
            lines.append(response.text)
    else:
        lines.append(response.text)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        headers = parse_headers(args.header)
        params = parse_queries(args.query)
        data, json_body = load_body(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.verbose:
        print(f"[{args.method}] {args.url}", file=sys.stderr)
        if params:
            print(f"  params:  {params}", file=sys.stderr)
        if headers:
            print(f"  headers: {headers}", file=sys.stderr)
        if json_body is not None:
            print(f"  json:    {json_body}", file=sys.stderr)
        elif data is not None:
            print(f"  data:    {data[:200]}", file=sys.stderr)

    start = time.perf_counter()
    try:
        response = requests.request(
            method=args.method,
            url=args.url,
            headers=headers or None,
            params=params or None,
            data=data,
            json=json_body,
            timeout=args.timeout,
            verify=not args.no_verify,
        )
    except requests.exceptions.Timeout:
        print(f"Error: request timed out after {args.timeout}s.", file=sys.stderr)
        return 1
    except requests.exceptions.ConnectionError as exc:
        print(f"Error: connection failed - {exc}", file=sys.stderr)
        return 1
    except requests.exceptions.RequestException as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    print(format_response(response, elapsed_ms))

    if args.save:
        save_path = Path(args.save).expanduser().resolve()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_bytes(response.content)
        print(f"\nResponse body saved to {save_path}.", file=sys.stderr)

    # Exit code reflects HTTP status category: 0 for 2xx, 1 otherwise.
    return 0 if response.ok else 1


if __name__ == "__main__":
    sys.exit(main())
