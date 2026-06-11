# sort-me-drive

> **Warning: This is an early-stage script. It modifies image files in place by
> writing EXIF metadata. Always run it on a copy of your photos, not on your
> only copy. Copy the target folder to a separate location first, verify the
> results there, and only then replace the originals if everything looks
> correct. Use `--dry-run` to preview changes before committing to anything.**

A CLI tool that fixes missing EXIF date metadata on photos imported from Google
Drive (or Google Photos) into Microsoft OneDrive.

## The Problem

When photos are migrated from Google Drive or Google Photos to OneDrive, many
lose their EXIF date fields (`DateTimeOriginal`, `CreateDate`, `ModifyDate`).
This is especially common with images received through messaging apps like
WhatsApp, Snapchat, and Facebook Messenger, which were processed by Google
Photos (identified by the `Software: Picasa` EXIF tag).

Without these date fields, OneDrive displays photos sorted by their import date
rather than the date they were actually taken or received. The result is a
timeline where years of photos appear to have been taken on the same day.

Photos taken directly with a phone camera (e.g., Samsung) are typically
unaffected, as they retain full EXIF metadata through the migration.

## How It Works

The tool relies on the folder structure that Google Drive uses to organize
photos: `YYYY/MM/filename`. This structure is treated as the source of truth for
the year and month, since users may have manually adjusted dates in Google Drive
before exporting.

For each file missing `DateTimeOriginal`, the tool:

1. Extracts the year and month from the `YYYY/MM` folder path.
2. Attempts to extract the day (and optionally the time) from the filename using
   known patterns (e.g., `IMG-YYYYMMDD-WA0001.jpg` for WhatsApp).
3. If the filename contains a date, it validates that the year and month match
   the folder. If they don't match, the filename date is discarded (the folder
   date takes precedence).
4. Falls back to the first of the month at midnight (`YYYY-MM-01 00:00:00`) when
   no day can be determined.
5. Writes `DateTimeOriginal`, `CreateDate`, and `ModifyDate` EXIF tags with the
   resolved date.

Files that already have `DateTimeOriginal` set are skipped entirely.

## Installation

Requires Python 3.10+ and [PDM](https://pdm-project.org/).

```
pdm install
```

## Usage

```
sort-me-drive [OPTIONS] <DIRECTORY>
```

### Arguments

- `DIRECTORY` -- Root directory to scan (required).

### Options

- `--dry-run` -- Show what would be changed without modifying any files.
- `-v`, `--verbose` -- Print detailed output for each file processed.
- `--extensions` -- Comma-separated list of file extensions to process.
  Defaults to `gif,heic,jpeg,jpg,mov,mp4,png,webp`.
- `--backup` -- Create `.bak` backup files before modifying originals.

### Examples

Preview what the tool would do without making changes:

```
pdm run sort-me-drive --dry-run -v ~/OneDrive/Pictures/Samsung\ Gallery/DCIM
```

Apply fixes to all files:

```
pdm run sort-me-drive ~/OneDrive/Pictures/Samsung\ Gallery/DCIM
```

Apply fixes and keep backups of every modified file:

```
pdm run sort-me-drive --backup ~/OneDrive/Pictures/Samsung\ Gallery/DCIM
```

Process only JPEG files:

```
pdm run sort-me-drive --extensions jpg,jpeg ~/OneDrive/Pictures/Samsung\ Gallery/DCIM
```

### Output

With `--verbose`, the tool prints a line for each file and a summary at the end:

```
Scanning: /home/user/OneDrive/Pictures/Samsung Gallery/DCIM
Found 2863 files, 641 missing DateTimeOriginal

Processing:
  ✓ 06/IMG-20220604-WA0020.jpg → 2022-06-04 00:00:00 (day from filename)
  ✓ 11/IMG-20190622-WA0003.jpg → 2021-11-01 00:00:00 (folder date only)
  ✓ 01/Snapchat-1665498557.jpg → 2020-01-01 00:00:00 (folder date only)
  ⊘ 01/20250101_120252.jpg     → skipped (already has DateTimeOriginal)

Summary:
  Fixed: 641
  Skipped (already had date): 2200
  Skipped (no folder date): 2
  Errors: 0
```

## Running Tests

```
pdm run pytest
```
