# Changelog

All notable changes to PyToolkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-13

### Added
- Initial release of PyToolkit.
- `file_renamer` - bulk file renaming with regex, prefix/suffix, case transforms, sequential numbering, and dry-run mode.
- `json_csv_converter` - bidirectional JSON/CSV conversion with nested JSON flattening and custom delimiters.
- `web_scraper` - simple web scraper built on `requests` + `BeautifulSoup` with CSS selector support and multiple output formats.
- `api_tester` - REST API testing tool supporting all HTTP methods, custom headers, request bodies, timing, and response saving.
- `text_cleaner` - text cleaning utility for whitespace, punctuation, emojis, URLs, HTML, digits, and case transformations.
- Full test suite using `pytest`.
- GitHub Actions CI workflow for Python 3.8-3.12.
