"""Date resolution from folder structure and filename patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Regex to find YYYY/MM pattern in a path (last occurrence wins)
FOLDER_DATE_RE = re.compile(r"(?:^|/)(\d{4})/(\d{2})(?:/|$)")

# Filename date patterns (order matters — first match wins)
FILENAME_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # IMG-YYYYMMDD-WA#### (WhatsApp)
    (re.compile(r"IMG-(\d{4})(\d{2})(\d{2})-WA", re.IGNORECASE), "whatsapp"),
    # YYYYMMDD_HHMMSS (Samsung / generic Android)
    (re.compile(r"(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})"), "timestamp"),
    # IMG_YYYYMMDD_HHMMSS
    (re.compile(r"IMG_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})", re.IGNORECASE), "img_timestamp"),
    # VID_YYYYMMDD_HHMMSS
    (re.compile(r"VID_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})", re.IGNORECASE), "vid_timestamp"),
]


@dataclass
class ResolvedDate:
    """Result of date resolution for a file."""

    date: datetime
    source: str  # "filename", "filename_day_only", "folder_fallback"
    folder_year: int
    folder_month: int


@dataclass
class FolderDate:
    """Year and month extracted from a folder path."""

    year: int
    month: int


def extract_folder_date(file_path: Path) -> FolderDate | None:
    """Extract YYYY/MM from the file's directory path.

    Uses the last occurrence of YYYY/MM in the path (closest to the file).
    Returns None if no pattern is found.
    """
    path_str = str(file_path)
    matches = list(FOLDER_DATE_RE.finditer(path_str))
    if not matches:
        return None

    last_match = matches[-1]
    year = int(last_match.group(1))
    month = int(last_match.group(2))

    if not (1 <= month <= 12):
        return None
    if year < 1900 or year > 2100:
        return None

    return FolderDate(year=year, month=month)


@dataclass
class FilenameDate:
    """Date components extracted from a filename."""

    year: int
    month: int
    day: int
    hour: int = 0
    minute: int = 0
    second: int = 0
    has_time: bool = False
    pattern_name: str = ""


def extract_filename_date(filename: str) -> FilenameDate | None:
    """Try to extract date components from a filename.

    Returns None if no recognizable date pattern is found.
    """
    for pattern, name in FILENAME_PATTERNS:
        match = pattern.search(filename)
        if not match:
            continue

        groups = match.groups()
        year, month, day = int(groups[0]), int(groups[1]), int(groups[2])

        if not (1 <= month <= 12 and 1 <= day <= 31):
            continue

        has_time = len(groups) >= 6
        hour = int(groups[3]) if has_time else 0
        minute = int(groups[4]) if has_time else 0
        second = int(groups[5]) if has_time else 0

        if has_time and not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
            continue

        return FilenameDate(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            second=second,
            has_time=has_time,
            pattern_name=name,
        )

    return None


def resolve_date(file_path: Path) -> ResolvedDate | None:
    """Resolve the date for a file using folder structure and filename.

    Returns None if no YYYY/MM folder pattern is found in the path.

    Strategy:
    1. Extract year/month from folder path (required)
    2. Try to extract day (and time) from filename
    3. If filename year/month matches folder, use filename date
    4. Otherwise, fall back to YYYY-MM-01 00:00:00
    """
    folder_date = extract_folder_date(file_path)
    if folder_date is None:
        return None

    filename = file_path.name
    filename_date = extract_filename_date(filename)

    if filename_date is not None:
        # Validate: filename year/month must match folder year/month
        if filename_date.year == folder_date.year and filename_date.month == folder_date.month:
            source = "filename" if filename_date.has_time else "filename_day_only"
            return ResolvedDate(
                date=datetime(
                    folder_date.year,
                    folder_date.month,
                    filename_date.day,
                    filename_date.hour,
                    filename_date.minute,
                    filename_date.second,
                ),
                source=source,
                folder_year=folder_date.year,
                folder_month=folder_date.month,
            )

    # Fallback: first of the month at midnight
    return ResolvedDate(
        date=datetime(folder_date.year, folder_date.month, 1, 0, 0, 0),
        source="folder_fallback",
        folder_year=folder_date.year,
        folder_month=folder_date.month,
    )
