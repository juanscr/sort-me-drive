"""CLI entry point for sort-me-drive."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sort_me_drive.date_resolver import resolve_date
from sort_me_drive.exif_writer import write_exif_dates
from sort_me_drive.logger import Logger
from sort_me_drive.scanner import DEFAULT_EXTENSIONS, scan_directory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sort-me-drive",
        description="Fix EXIF date metadata on photos imported from Google Drive to OneDrive.",
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Root directory to scan",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print detailed output for each file processed",
    )
    parser.add_argument(
        "--extensions",
        type=str,
        default=None,
        help=f"Comma-separated list of file extensions to process (default: {','.join(sorted(DEFAULT_EXTENSIONS))})",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create .bak backup files before modifying",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    directory: Path = args.directory.resolve()
    if not directory.is_dir():
        print(f"Error: '{directory}' is not a directory", file=sys.stderr)
        return 1

    extensions: set[str] | None = None
    if args.extensions:
        extensions = {e.strip().lower().lstrip(".") for e in args.extensions.split(",")}

    logger = Logger(verbose=args.verbose)

    # Phase 1: Scan
    logger.scanning(directory)
    scan_result = scan_directory(directory, extensions)
    logger.scan_summary(scan_result.total_files, len(scan_result.to_process))
    logger.stats.skipped_has_date = len(scan_result.skipped_has_date)

    if not scan_result.to_process:
        print("Nothing to process.")
        logger.print_summary(dry_run=args.dry_run)
        return 0

    # Phase 2: Process files
    if args.verbose:
        print("Processing:")

    for file_path in scan_result.to_process:
        resolved = resolve_date(file_path)

        if resolved is None:
            logger.skipped_no_folder(file_path)
            continue

        source_label = _source_label(resolved.source)
        result = write_exif_dates(
            file_path,
            resolved.date,
            backup=args.backup,
            dry_run=args.dry_run,
        )

        if not result.success:
            logger.error(file_path, result.error or "unknown error")
            continue

        logger.fixed(file_path, resolved.date, source_label)

    if args.verbose:
        for file_path in scan_result.skipped_has_date:
            logger.skipped_has_date(file_path)
        logger.stats.skipped_has_date = len(scan_result.skipped_has_date)

    logger.print_summary(dry_run=args.dry_run)
    return 0


def _source_label(source: str) -> str:
    """Convert internal source name to a human-readable label."""
    labels = {
        "filename": "day+time from filename",
        "filename_day_only": "day from filename",
        "folder_fallback": "folder date only",
    }
    return labels.get(source, source)


if __name__ == "__main__":
    sys.exit(main())
