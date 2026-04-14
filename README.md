# PyToolkit

> A collection of five practical, well-tested Python CLI tools for everyday developer tasks.

[![Tests](https://github.com/alperenakin/PyToolkit/actions/workflows/tests.yml/badge.svg)](https://github.com/alperenakin/PyToolkit/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

PyToolkit is a set of five small Python CLI tools I use for everyday
automation: bulk file renaming, format conversion, web scraping, API testing
and text cleaning. Each tool is a standalone script with an `argparse`
interface, error handling, and tests.

---

## Table of contents

- [Tools](#tools)
- [Installation](#installation)
- [Usage](#usage)
  - [file_renamer](#1-file_renamer--bulk-file-renaming)
  - [json_csv_converter](#2-json_csv_converter--json--csv-conversion)
  - [web_scraper](#3-web_scraper--simple-web-scraper)
  - [api_tester](#4-api_tester--rest-api-testing)
  - [text_cleaner](#5-text_cleaner--text-cleaning--normalization)
- [Project layout](#project-layout)
- [Running the tests](#running-the-tests)
- [Contributing](#contributing)
- [License](#license)

---

## Tools

| Tool | Purpose | Key flags |
|------|---------|-----------|
| **file_renamer** | Bulk-rename files with regex, prefix/suffix, case changes, or sequential numbering. | `--pattern`, `--replace`, `--prefix`, `--sequence`, `--dry-run` |
| **json_csv_converter** | Convert between JSON (array of objects) and CSV, both directions. | `--input`, `--output`, `--direction`, `--flatten`, `--delimiter` |
| **web_scraper** | Fetch a URL and extract elements via CSS selectors. | `--url`, `--selector`, `--attr`, `--format` |
| **api_tester** | Issue HTTP requests and inspect responses with timing and pretty-printing. | `--url`, `--method`, `--header`, `--json`, `--save` |
| **text_cleaner** | Clean text: strip whitespace, punctuation, emojis, URLs, HTML tags, digits. | `--normalize-spaces`, `--remove-emoji`, `--strip-html`, `--lowercase` |

---

## Installation

### Option A - clone and install dependencies

```bash
git clone https://github.com/alperenakin/PyToolkit.git
cd PyToolkit
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

You can now run any tool as a Python module:

```bash
python -m tools.file_renamer --help
```

### Option B - install as a package (gives you short CLI commands)

```bash
pip install -e .
```

After the editable install, each tool is available as a short command:

```bash
file-renamer --help
json-csv     --help
web-scraper  --help
api-tester   --help
text-cleaner --help
```

### Requirements

- Python 3.8 or newer
- `requests` >= 2.31
- `beautifulsoup4` >= 4.12
- `pytest` >= 7.4 (for running the tests)

---

## Usage

All five tools accept `--help` / `-h` for full documentation. The snippets below
highlight the most common recipes.

### 1. `file_renamer` - bulk file renaming

Rename files using regex, prefix, suffix, case transforms, or sequential
numbering. Always preview with `--dry-run` first.

```bash
# Replace "IMG_" with "photo_" in all .jpg files
python -m tools.file_renamer \
    --dir ./photos \
    --pattern "IMG_" --replace "photo_" \
    --ext .jpg

# Add a date prefix, lowercase the stem, recurse into subfolders (preview only)
python -m tools.file_renamer \
    --dir ./docs \
    --prefix "2026_" --lowercase \
    --recursive --dry-run

# Number all PDFs sequentially: scan_001.pdf, scan_002.pdf, ...
python -m tools.file_renamer \
    --dir ./scans \
    --glob "*.pdf" \
    --sequence "scan_{n:03d}"
```

Flags of note:

- `--pattern` / `--replace` - regex find/replace on the filename stem.
- `--prefix` / `--suffix` - prepend/append strings (suffix goes before the extension).
- `--lowercase` / `--uppercase` / `--titlecase` - case transformations.
- `--sequence "pattern_{n:03d}"` - sequential rename with zero-padded numbering.
- `--recursive` - descend into subdirectories.
- `--dry-run` - print what *would* happen without touching anything.

### 2. `json_csv_converter` - JSON <-> CSV conversion

Bidirectional conversion with auto-detection from file extensions.

```bash
# JSON -> CSV
python -m tools.json_csv_converter -i data.json -o data.csv

# CSV -> JSON with pretty printing
python -m tools.json_csv_converter -i users.csv -o users.json --pretty

# Flatten nested JSON ({"user": {"name": "Ada"}} -> user.name)
python -m tools.json_csv_converter -i nested.json -o flat.csv --flatten

# European-style semicolon CSV
python -m tools.json_csv_converter -i data.json -o data.csv --delimiter ";"
```

Handles heterogeneous rows (union of keys) and serialises nested values as
embedded JSON so the data round-trips cleanly.

### 3. `web_scraper` - simple web scraper

Fetch a page with `requests`, parse it with `BeautifulSoup`, select elements
with CSS selectors, and output JSON, CSV, or plain text.

```bash
# Grab all H2 titles
python -m tools.web_scraper \
    --url https://example.com \
    --selector "h2.title"

# Extract outbound links to JSON
python -m tools.web_scraper \
    --url https://example.com \
    --selector "a" --attr href \
    --format json -o links.json

# Custom User-Agent, timeout, and result limit
python -m tools.web_scraper \
    --url https://example.com/shop \
    --selector "div.product > h3" \
    --user-agent "PyToolkit/1.0" \
    --timeout 15 --limit 20
```

> Respect each site's `robots.txt` and terms of service.

### 4. `api_tester` - REST API testing

Issue any HTTP method with custom headers, query params, and body payloads.
The tool prints the status code, response headers, body (pretty-printed if
JSON), and request elapsed time.

```bash
# Simple GET
python -m tools.api_tester -u https://api.github.com/users/octocat

# POST with a JSON body and custom header
python -m tools.api_tester \
    -u https://httpbin.org/post -X POST \
    --json '{"name": "Alperen"}' \
    --header "X-Api-Key: secret"

# PUT body from a file, save response body to disk
python -m tools.api_tester \
    -u https://httpbin.org/put -X PUT \
    --data-file examples/api_tester/payload.json \
    --save response.json

# Query parameters (repeatable)
python -m tools.api_tester \
    -u https://httpbin.org/get \
    -q limit=10 -q page=2
```

The exit code is `0` for 2xx responses, `1` otherwise - handy in shell scripts.

### 5. `text_cleaner` - text cleaning & normalization

Compose a cleaning pipeline from a collection of independent flags. Reads from
a file or stdin; writes to a file or stdout.

```bash
# Trim whitespace, lowercase everything
python -m tools.text_cleaner \
    -i dirty.txt -o clean.txt \
    --normalize-spaces --lowercase

# Strip HTML tags, URLs, and emojis in one pass
python -m tools.text_cleaner \
    -i post.html -o post.txt \
    --strip-html --remove-urls --remove-emoji

# Pipe from stdin to stdout
echo "Hello   WORLD 😀" | python -m tools.text_cleaner \
    --normalize-spaces --remove-emoji
```

Available operations: `--remove-emoji`, `--remove-urls`, `--strip-html`,
`--remove-punct`, `--remove-digits`, `--normalize-spaces`, `--collapse-newlines`,
`--normalize-unicode`, `--lowercase` / `--uppercase`, `--trim`.

---

## Project layout

```
PyToolkit/
├── tools/                          # The five CLI tools
│   ├── __init__.py
│   ├── file_renamer.py
│   ├── json_csv_converter.py
│   ├── web_scraper.py
│   ├── api_tester.py
│   └── text_cleaner.py
├── examples/                       # Sample inputs, outputs, and recipes
│   ├── file_renamer/
│   ├── json_csv_converter/
│   ├── web_scraper/
│   ├── api_tester/
│   └── text_cleaner/
├── tests/                          # pytest test suite
│   ├── conftest.py
│   ├── test_file_renamer.py
│   ├── test_json_csv_converter.py
│   ├── test_web_scraper.py
│   ├── test_api_tester.py
│   └── test_text_cleaner.py
├── .github/workflows/tests.yml     # CI: tests on Python 3.8-3.12
├── requirements.txt
├── pyproject.toml                  # Packaging + CLI entry points
├── CHANGELOG.md
├── LICENSE                         # MIT
├── .gitignore
└── README.md
```

---

## Running the tests

```bash
pip install -r requirements.txt
pytest
```

The test suite is offline-safe: `web_scraper` and `api_tester` tests replace
`requests` with stubs so nothing hits the network.

CI runs the same suite on every push across Python 3.8, 3.9, 3.10, 3.11, and
3.12 and additionally smoke-tests each CLI's `--help` output.

---

## Contributing

This repository is a personal portfolio project, but issues and pull requests
are welcome. If you add a new tool or flag:

1. Keep the `argparse` surface consistent (long form + short form where sensible).
2. Add tests - the suite must stay offline-safe.
3. Update the README and `CHANGELOG.md`.

---

## License

Released under the [MIT License](LICENSE). © 2026 Alperen Akın.
