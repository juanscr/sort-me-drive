"""Structured output and logging."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Stats:
    """Processing statistics."""

    fixed: int = 0
    skipped_has_date: int = 0
    skipped_no_folder: int = 0
    errors: int = 0
    error_details: list[tuple[Path, str]] = field(default_factory=list)


class Logger:
    """Structured output for sort-me-drive."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.stats = Stats()

    def scanning(self, directory: Path) -> None:
        print(f"Scanning: {directory}")

    def scan_summary(self, total: int, to_process: int) -> None:
        print(f"Found {total} files, {to_process} missing DateTimeOriginal\n")

    def fixed(self, file_path: Path, date: datetime, source: str) -> None:
        self.stats.fixed += 1
        if self.verbose:
            rel = _short_path(file_path)
            date_str = date.strftime("%Y-%m-%d %H:%M:%S")
            print(f"  ✓ {rel} → {date_str} ({source})")

    def skipped_has_date(self, file_path: Path) -> None:
        self.stats.skipped_has_date += 1
        if self.verbose:
            rel = _short_path(file_path)
            print(f"  ⊘ {rel} → skipped (already has DateTimeOriginal)")

    def skipped_no_folder(self, file_path: Path) -> None:
        self.stats.skipped_no_folder += 1
        if self.verbose:
            rel = _short_path(file_path)
            print(f"  ⚠ {rel} → skipped (no YYYY/MM folder structure)")

    def error(self, file_path: Path, message: str) -> None:
        self.stats.errors += 1
        self.stats.error_details.append((file_path, message))
        rel = _short_path(file_path)
        print(f"  ✗ {rel} → error: {message}", file=sys.stderr)

    def print_summary(self, dry_run: bool = False) -> None:
        prefix = "[DRY RUN] " if dry_run else ""
        print(f"\n{prefix}Summary:")
        print(f"  Fixed: {self.stats.fixed}")
        print(f"  Skipped (already had date): {self.stats.skipped_has_date}")
        print(f"  Skipped (no folder date): {self.stats.skipped_no_folder}")
        print(f"  Errors: {self.stats.errors}")

        if self.stats.error_details:
            print("\nError details:")
            for path, msg in self.stats.error_details:
                print(f"  {_short_path(path)}: {msg}")


def _short_path(file_path: Path) -> str:
    """Return a short representation of a path, showing last 3 components."""
    parts = file_path.parts
    if len(parts) > 3:
        return str(Path(*parts[-3:]))
    return str(file_path)
