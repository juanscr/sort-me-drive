"""EXIF metadata writing."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import piexif


EXIF_DATE_FORMAT = "%Y:%m:%d %H:%M:%S"


@dataclass
class WriteResult:
    """Result of writing EXIF data to a file."""

    success: bool
    file_path: Path
    error: str | None = None


def format_exif_date(dt: datetime) -> bytes:
    """Format a datetime as an EXIF date string."""
    return dt.strftime(EXIF_DATE_FORMAT).encode("ascii")


def write_exif_dates(
    file_path: Path,
    date: datetime,
    backup: bool = False,
    dry_run: bool = False,
) -> WriteResult:
    """Write DateTimeOriginal, CreateDate, and ModifyDate EXIF tags to a file.

    Args:
        file_path: Path to the image file.
        date: The date to write.
        backup: If True, create a .bak file before modifying.
        dry_run: If True, don't actually modify the file.

    Returns:
        WriteResult indicating success or failure.
    """
    if dry_run:
        return WriteResult(success=True, file_path=file_path)

    try:
        # Load existing EXIF data (or create empty)
        try:
            exif_data = piexif.load(str(file_path))
        except Exception:
            exif_data = {"0th": {}, "Exif": {}, "1st": {}, "GPS": {}}

        date_bytes = format_exif_date(date)

        # Set all three date fields
        exif_data.setdefault("Exif", {})[piexif.ExifIFD.DateTimeOriginal] = date_bytes
        exif_data.setdefault("Exif", {})[piexif.ExifIFD.DateTimeDigitized] = date_bytes
        exif_data.setdefault("0th", {})[piexif.ImageIFD.DateTime] = date_bytes

        if backup:
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            shutil.copy2(str(file_path), str(backup_path))

        exif_bytes = piexif.dump(exif_data)
        piexif.insert(exif_bytes, str(file_path))

        return WriteResult(success=True, file_path=file_path)

    except PermissionError:
        return WriteResult(
            success=False,
            file_path=file_path,
            error="Permission denied",
        )
    except Exception as e:
        return WriteResult(
            success=False,
            file_path=file_path,
            error=str(e),
        )
