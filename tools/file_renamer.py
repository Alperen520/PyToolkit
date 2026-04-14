#!/usr/bin/env python3
"""
file_renamer.py - Bulk file renaming tool.

Rename files in a directory using regex substitution, prefix/suffix addition,
case transformation, or sequential numbering. Always preview changes with
``--dry-run`` before applying.

Examples:
    # Replace "IMG_" with "photo_" in all .jpg files
    python -m tools.file_renamer --dir ./photos --pattern "IMG_" --replace "photo_" --ext .jpg

    # Add a prefix and lowercase everything, dry-run first
    python -m tools.file_renamer --dir ./docs --prefix "2026_" --lowercase --dry-run

    # Sequentially number files matching a glob
    python -m tools.file_renamer --dir ./scans --glob "*.pdf" --sequence "scan_{n:03d}"
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="file-renamer",
        description="Bulk-rename files with regex, prefix/suffix, case, or numbering.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  file-renamer --dir ./photos --pattern 'IMG_' --replace 'photo_' --ext .jpg\n"
            "  file-renamer --dir ./docs --prefix '2026_' --lowercase --dry-run\n"
            "  file-renamer --dir ./scans --glob '*.pdf' --sequence 'scan_{n:03d}'\n"
        ),
    )
    parser.add_argument("--dir", "-d", required=True, help="Target directory.")
    parser.add_argument("--glob", "-g", default="*", help="Glob pattern for selecting files (default: '*').")
    parser.add_argument("--ext", "-e", help="Restrict to files with this extension (e.g., .jpg).")
    parser.add_argument("--recursive", "-r", action="store_true", help="Descend into subdirectories.")

    parser.add_argument("--pattern", "-p", help="Regex pattern to find in filenames.")
    parser.add_argument("--replace", default="", help="Replacement string (use with --pattern).")

    parser.add_argument("--prefix", help="String to prepend to each filename.")
    parser.add_argument("--suffix", help="String to append before the extension.")

    case_group = parser.add_mutually_exclusive_group()
    case_group.add_argument("--lowercase", action="store_true", help="Convert filename to lowercase.")
    case_group.add_argument("--uppercase", action="store_true", help="Convert filename to uppercase.")
    case_group.add_argument("--titlecase", action="store_true", help="Convert filename to Title Case.")

    parser.add_argument(
        "--sequence",
        help="Rename files sequentially using a format string containing '{n}', e.g. 'img_{n:03d}'.",
    )
    parser.add_argument("--start", type=int, default=1, help="Starting number for --sequence (default: 1).")

    parser.add_argument("--dry-run", "-n", action="store_true", help="Preview changes without touching the filesystem.")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress per-file output.")
    return parser


def collect_files(directory: Path, glob: str, ext: str | None, recursive: bool) -> List[Path]:
    """Return the sorted list of files in *directory* that match the filters."""
    iterator = directory.rglob(glob) if recursive else directory.glob(glob)
    files = [f for f in iterator if f.is_file()]
    if ext:
        ext_normalized = ext if ext.startswith(".") else f".{ext}"
        files = [f for f in files if f.suffix.lower() == ext_normalized.lower()]
    return sorted(files)


def transform_name(stem: str, args: argparse.Namespace) -> str:
    """Apply regex/prefix/suffix/case transformations to a filename *stem*."""
    new = stem
    if args.pattern:
        new = re.sub(args.pattern, args.replace, new)
    if args.prefix:
        new = f"{args.prefix}{new}"
    if args.suffix:
        new = f"{new}{args.suffix}"
    if args.lowercase:
        new = new.lower()
    elif args.uppercase:
        new = new.upper()
    elif args.titlecase:
        new = new.title()
    return new


def plan_renames(files: List[Path], args: argparse.Namespace) -> List[Tuple[Path, Path]]:
    """Build a list of (old_path, new_path) pairs to execute."""
    plan: List[Tuple[Path, Path]] = []
    counter = args.start
    for path in files:
        if args.sequence:
            try:
                new_stem = args.sequence.format(n=counter)
            except (KeyError, IndexError) as exc:
                raise ValueError(
                    f"Invalid --sequence format '{args.sequence}': must contain '{{n}}'."
                ) from exc
            counter += 1
        else:
            new_stem = transform_name(path.stem, args)

        new_name = f"{new_stem}{path.suffix}"
        new_path = path.with_name(new_name)
        if new_path != path:
            plan.append((path, new_path))
    return plan


def apply_plan(plan: List[Tuple[Path, Path]], dry_run: bool, quiet: bool) -> int:
    """Execute the rename *plan*. Returns count of renamed files."""
    renamed = 0
    for old, new in plan:
        if new.exists():
            print(f"SKIP  {old.name} -> {new.name} (target exists)", file=sys.stderr)
            continue
        prefix = "[DRY] " if dry_run else ""
        if not quiet:
            print(f"{prefix}{old.name}  ->  {new.name}")
        if not dry_run:
            old.rename(new)
        renamed += 1
    return renamed


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    directory = Path(args.dir).expanduser().resolve()
    if not directory.is_dir():
        print(f"Error: '{directory}' is not a directory.", file=sys.stderr)
        return 2

    if not any([args.pattern, args.prefix, args.suffix, args.lowercase,
                args.uppercase, args.titlecase, args.sequence]):
        print("Error: no transformation specified. Use --help for options.", file=sys.stderr)
        return 2

    try:
        files = collect_files(directory, args.glob, args.ext, args.recursive)
    except OSError as exc:
        print(f"Error reading directory: {exc}", file=sys.stderr)
        return 1

    if not files:
        print("No matching files found.", file=sys.stderr)
        return 0

    try:
        plan = plan_renames(files, args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if not plan:
        print("Nothing to rename (names already match the target transformation).")
        return 0

    try:
        count = apply_plan(plan, args.dry_run, args.quiet)
    except OSError as exc:
        print(f"Error while renaming: {exc}", file=sys.stderr)
        return 1

    verb = "Would rename" if args.dry_run else "Renamed"
    print(f"\n{verb} {count} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
