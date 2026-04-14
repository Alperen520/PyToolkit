# file_renamer - examples

Quick recipes for common bulk-rename tasks. Always pair the first run with
`--dry-run` so you can preview changes before touching the filesystem.

## 1. Replace a substring

```bash
python -m tools.file_renamer \
    --dir ./photos \
    --pattern "IMG_" \
    --replace "photo_" \
    --ext .jpg
```

**Before**: `IMG_001.jpg`, `IMG_002.jpg`
**After**:  `photo_001.jpg`, `photo_002.jpg`

## 2. Add a date prefix and lowercase everything

```bash
python -m tools.file_renamer \
    --dir ./docs \
    --prefix "2026-04-13_" \
    --lowercase \
    --dry-run
```

**Before**: `Report.PDF`, `Notes.TXT`
**After**:  `2026-04-13_report.PDF`, `2026-04-13_notes.TXT`

> Note: only the *stem* is lowercased; the extension is preserved as-is.

## 3. Sequential numbering

```bash
python -m tools.file_renamer \
    --dir ./scans \
    --glob "*.pdf" \
    --sequence "scan_{n:03d}" \
    --start 1
```

**Before**: `a.pdf`, `b.pdf`, `c.pdf`
**After**:  `scan_001.pdf`, `scan_002.pdf`, `scan_003.pdf`

## 4. Recursive regex rename

```bash
python -m tools.file_renamer \
    --dir ./project \
    --pattern "([0-9]{4})-([0-9]{2})" \
    --replace "\2-\1" \
    --recursive
```

Swaps `YYYY-MM` prefixes to `MM-YYYY` across every subdirectory.
