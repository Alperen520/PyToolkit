#!/usr/bin/env python3
"""
text_cleaner.py - Text cleaning and normalization tool.

Clean up text by removing extra whitespace, punctuation, emojis, URLs, HTML
tags, or digits. Combine flags to build a custom cleaning pipeline.

Examples:
    # Trim whitespace and lowercase
    python -m tools.text_cleaner -i dirty.txt -o clean.txt --normalize-spaces --lowercase

    # Remove emojis, URLs, and HTML tags
    python -m tools.text_cleaner -i post.html -o post.txt --strip-html --remove-urls --remove-emoji

    # Read from stdin, write to stdout
    echo "Hello   WORLD 😀" | python -m tools.text_cleaner --normalize-spaces --remove-emoji
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path


# Emoji ranges covering the common Unicode blocks. Not exhaustive but catches
# 99% of real-world emoji in user-generated text.
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F700-\U0001F77F"  # alchemical
    "\U0001F780-\U0001F7FF"  # geometric shapes
    "\U0001F800-\U0001F8FF"  # supplemental arrows
    "\U0001F900-\U0001F9FF"  # supplemental symbols & pictographs
    "\U0001FA00-\U0001FA6F"  # chess / medical
    "\U0001FA70-\U0001FAFF"  # symbols & pictographs extended-A
    "\U00002702-\U000027B0"  # dingbats
    "\U000024C2-\U0001F251"  # enclosed characters
    "]+",
    flags=re.UNICODE,
)

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
PUNCTUATION_PATTERN = re.compile(r"[^\w\s]", re.UNICODE)
DIGIT_PATTERN = re.compile(r"\d+")
MULTI_WHITESPACE_PATTERN = re.compile(r"\s+")
MULTI_NEWLINE_PATTERN = re.compile(r"\n\s*\n\s*\n+")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="text-cleaner",
        description="Clean text by stripping unwanted elements and normalising formatting.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  text-cleaner -i dirty.txt -o clean.txt --normalize-spaces --lowercase\n"
            "  echo 'Hello 😀' | text-cleaner --remove-emoji\n"
        ),
    )
    parser.add_argument("--input", "-i", help="Input file path (default: stdin).")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout).")

    parser.add_argument("--remove-emoji", action="store_true", help="Strip emoji characters.")
    parser.add_argument("--remove-urls", action="store_true", help="Strip http(s) URLs and www.* links.")
    parser.add_argument("--strip-html", action="store_true", help="Remove HTML/XML tags.")
    parser.add_argument("--remove-punct", action="store_true", help="Remove punctuation characters.")
    parser.add_argument("--remove-digits", action="store_true", help="Remove digit characters.")
    parser.add_argument("--normalize-spaces", action="store_true", help="Collapse repeated whitespace into single spaces.")
    parser.add_argument("--collapse-newlines", action="store_true", help="Collapse 3+ consecutive newlines into two.")
    parser.add_argument("--normalize-unicode", action="store_true", help="Apply NFKC Unicode normalization.")

    case_group = parser.add_mutually_exclusive_group()
    case_group.add_argument("--lowercase", action="store_true", help="Convert to lowercase.")
    case_group.add_argument("--uppercase", action="store_true", help="Convert to uppercase.")

    parser.add_argument("--trim", action="store_true", help="Strip leading/trailing whitespace from each line.")
    parser.add_argument("--encoding", default="utf-8", help="File encoding (default: utf-8).")
    return parser


def clean(text: str, args: argparse.Namespace) -> str:
    """Apply every cleaning operation flagged on *args* to *text*."""
    if args.normalize_unicode:
        text = unicodedata.normalize("NFKC", text)
    if args.strip_html:
        text = HTML_TAG_PATTERN.sub("", text)
    if args.remove_urls:
        text = URL_PATTERN.sub("", text)
    if args.remove_emoji:
        text = EMOJI_PATTERN.sub("", text)
    if args.remove_digits:
        text = DIGIT_PATTERN.sub("", text)
    if args.remove_punct:
        text = PUNCTUATION_PATTERN.sub("", text)
    if args.trim:
        text = "\n".join(line.strip() for line in text.splitlines())
    if args.collapse_newlines:
        text = MULTI_NEWLINE_PATTERN.sub("\n\n", text)
    if args.normalize_spaces:
        # Preserve newlines while collapsing other whitespace runs.
        text = "\n".join(
            MULTI_WHITESPACE_PATTERN.sub(" ", line).strip()
            for line in text.splitlines()
        )
    if args.lowercase:
        text = text.lower()
    elif args.uppercase:
        text = text.upper()
    return text


def read_input(path: str | None, encoding: str) -> str:
    if path is None:
        return sys.stdin.read()
    input_path = Path(path).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file '{input_path}' not found.")
    return input_path.read_text(encoding=encoding)


def write_output(text: str, path: str | None, encoding: str) -> None:
    if path is None:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
        return
    output_path = Path(path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding=encoding)


def any_operation_selected(args: argparse.Namespace) -> bool:
    """True if the user actually asked for a transformation."""
    return any([
        args.remove_emoji, args.remove_urls, args.strip_html,
        args.remove_punct, args.remove_digits, args.normalize_spaces,
        args.collapse_newlines, args.normalize_unicode,
        args.lowercase, args.uppercase, args.trim,
    ])


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not any_operation_selected(args):
        print("Error: no cleaning operation specified. Use --help to see options.", file=sys.stderr)
        return 2

    try:
        text = read_input(args.input, args.encoding)
    except (FileNotFoundError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    cleaned = clean(text, args)

    try:
        write_output(cleaned, args.output, args.encoding)
    except OSError as exc:
        print(f"Error writing output: {exc}", file=sys.stderr)
        return 1

    if args.output:
        chars_in, chars_out = len(text), len(cleaned)
        delta = chars_in - chars_out
        print(
            f"Cleaned: {chars_in} -> {chars_out} chars ({delta:+d}). Saved to {args.output}.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
