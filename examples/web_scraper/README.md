# web_scraper - examples

## 1. Grab every H2 from a page

```bash
python -m tools.web_scraper \
    --url https://example.com \
    --selector "h2" \
    --format json \
    --output titles.json
```

## 2. Extract outbound links

```bash
python -m tools.web_scraper \
    --url https://example.com \
    --selector "a" \
    --attr href \
    --format csv \
    --output links.csv
```

## 3. Scrape product names with a custom selector

```bash
python -m tools.web_scraper \
    --url https://example.com/shop \
    --selector "div.product > h3.name" \
    --limit 20 \
    --user-agent "PyToolkit/1.0" \
    --timeout 15
```

## 4. Polite defaults

The tool ships with a descriptive `User-Agent` and a default 10-second timeout.
Respect each site's `robots.txt` and rate limits - this tool is intentionally
simple and does not retry, rotate proxies, or bypass bot protection.
