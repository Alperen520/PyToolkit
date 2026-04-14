#!/usr/bin/env python3
"""
json_csv_converter.py - Bidirectional JSON <-> CSV converter.

Convert between JSON (array of objects) and CSV. Direction is auto-detected
from file extensions but can be forced with ``--direction``.

Examples:
    # JSON -> CSV (auto-detected)
    python -m tools.json_csv_converter -i data.json -o data.csv

    # CSV -> JSON with pretty printing
    python -m tools.json_csv_converter -i users.csv -o users.json --pretty

    # Flatten nested JSON to CSV
    python -m tools.json_csv_converter -i nested.json -o flat.csv --flatten

    # Use semicolon delimiter for European-style CSV
    python -m tools.json_csv_converter -i data.json -o data.csv --delimiter ";"
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="json-csv",
        description="Convert between JSON and CSV formats.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  json-csv -i data.json -o data.csv\n"
            "  json-csv -i users.csv -o users.json --pretty\n"
            "  json-csv -i nested.json -o flat.csv --flatten\n"
        ),
    )
    parser.add_argument("--input", "-i", required=True, help="Input file path.")
    parser.add_argument("--output", "-o", required=True, help="Output file path.")
    parser.add_argument(
        "--direction",
        choices=["j2c", "c2j", "auto"],
        default="auto",
        help="Conversion direction: j2c (JSON->CSV), c2j (CSV->JSON), or auto (default).",
    )
    parser.add_argument("--delimiter", default=",", help="CSV delimiter (default: ',').")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output with indentation.")
    parser.add_argument("--flatten", action="store_true", help="Flatten nested JSON objects using dot-notation keys.")
    parser.add_argument("--encoding", default="utf-8", help="File encoding (default: utf-8).")
    return parser


def detect_direction(input_path: Path, output_path: Path) -> str:
    """Infer conversion direction from file extensions."""
    in_ext = input_path.suffix.lower()
    out_ext = output_path.suffix.lower()
    if in_ext == ".json" and out_ext == ".csv":
        return "j2c"
    if in_ext == ".csv" and out_ext == ".json":
        return "c2j"
    raise ValueError(
        f"Cannot auto-detect direction from extensions ({in_ext} -> {out_ext}). "
        "Use --direction j2c or --direction c2j."
    )


def flatten_dict(obj: Any, prefix: str = "", separator: str = ".") -> Dict[str, Any]:
    """Recursively flatten a nested dict using dotted keys."""
    flat: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_key = f"{prefix}{separator}{key}" if prefix else key
            flat.update(flatten_dict(value, new_key, separator))
    elif isinstance(obj, list):
        flat[prefix] = json.dumps(obj, ensure_ascii=False)
    else:
        flat[prefix] = obj
    return flat


def json_to_csv(input_path: Path, output_path: Path, delimiter: str,
                flatten: bool, encoding: str) -> int:
    """Convert a JSON array of objects to CSV. Returns row count."""
    with input_path.open("r", encoding=encoding) as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON input must be an array of objects to convert to CSV.")

    if not data:
        output_path.write_text("", encoding=encoding)
        return 0

    rows: List[Dict[str, Any]] = [flatten_dict(r) if flatten else r for r in data]

    # Collect the union of all keys so rows with different shapes still line up.
    fieldnames: List[str] = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each JSON array element must be an object.")
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)

    with output_path.open("w", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        for row in rows:
            # DictWriter will raise on unknown keys; flatten guarantees strings.
            writer.writerow({k: _csv_value(row.get(k, "")) for k in fieldnames})

    return len(rows)


def _csv_value(value: Any) -> Any:
    """Serialise non-scalar CSV values as JSON so they round-trip cleanly."""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return ""
    return value


def csv_to_json(input_path: Path, output_path: Path, delimiter: str,
                pretty: bool, encoding: str) -> int:
    """Convert CSV to JSON array. Returns row count."""
    with input_path.open("r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        rows = [dict(row) for row in reader]

    with output_path.open("w", encoding=encoding) as f:
        if pretty:
            json.dump(rows, f, indent=2, ensure_ascii=False)
        else:
            json.dump(rows, f, ensure_ascii=False)

    return len(rows)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not input_path.is_file():
        print(f"Error: input file '{input_path}' not found.", file=sys.stderr)
        return 2

    direction = args.direction
    if direction == "auto":
        try:
            direction = detect_direction(input_path, output_path)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        if direction == "j2c":
            count = json_to_csv(input_path, output_path, args.delimiter, args.flatten, args.encoding)
            print(f"Wrote {count} row(s) to {output_path} (JSON -> CSV).")
        else:
            count = csv_to_json(input_path, output_path, args.delimiter, args.pretty, args.encoding)
            print(f"Wrote {count} row(s) to {output_path} (CSV -> JSON).")
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Error parsing input: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Error reading/writing file: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
