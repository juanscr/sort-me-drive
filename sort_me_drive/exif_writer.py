"""EXIF/metadata date writing for multiple file formats.

Supports:
- JPEG: piexif (native EXIF)
- PNG/WEBP/GIF: Pillow (EXIF embedding)
- MP4/MOV: mutagen (QuickTime/MP4 metadata)
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import piexif
from PIL import Image
from mutagen.mp4 import MP4

EXIF_DATE_FORMAT = "%Y:%m:%d %H:%M:%S"

# File types by writing strategy
PIEXIF_EXTENSIONS = {".jpg", ".jpeg"}
PILLOW_EXTENSIONS = {".png", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".mov"}
SUPPORTED_EXTENSIONS = PIEXIF_EXTENSIONS | PILLOW_EXTENSIONS | VIDEO_EXTENSIONS


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
    """Write date metadata to a file, dispatching by format.

    Args:
        file_path: Path to the image/video file.
        date: The date to write.
        backup: If True, create a .bak file before modifying.
        dry_run: If True, don't actually modify the file.

    Returns:
        WriteResult indicating success or failure.
    """
    if dry_run:
        return WriteResult(success=True, file_path=file_path)

    ext = file_path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return WriteResult(
            success=False,
            file_path=file_path,
            error=f"unsupported format: {ext}",
        )

    try:
        if backup:
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            shutil.copy2(str(file_path), str(backup_path))

        if ext in PIEXIF_EXTENSIONS:
            return _write_jpeg(file_path, date)
        elif ext in PILLOW_EXTENSIONS:
            return _write_pillow(file_path, date)
        elif ext in VIDEO_EXTENSIONS:
            return _write_video(file_path, date)
        else:
            return WriteResult(
                success=False,
                file_path=file_path,
                error=f"unsupported format: {ext}",
            )

    except PermissionError:
        return WriteResult(success=False, file_path=file_path, error="permission denied")
    except Exception as e:
        return WriteResult(
            success=False,
            file_path=file_path,
            error=f"{type(e).__name__}: {e}",
        )


def _write_jpeg(file_path: Path, date: datetime) -> WriteResult:
    """Write EXIF dates to a JPEG file using piexif."""
    try:
        exif_data = piexif.load(str(file_path))
    except Exception:
        exif_data = {"0th": {}, "Exif": {}, "1st": {}, "GPS": {}}

    date_bytes = format_exif_date(date)

    exif_data.setdefault("Exif", {})[piexif.ExifIFD.DateTimeOriginal] = date_bytes
    exif_data.setdefault("Exif", {})[piexif.ExifIFD.DateTimeDigitized] = date_bytes
    exif_data.setdefault("0th", {})[piexif.ImageIFD.DateTime] = date_bytes

    exif_bytes = piexif.dump(exif_data)
    piexif.insert(exif_bytes, str(file_path))

    return WriteResult(success=True, file_path=file_path)


def _write_pillow(file_path: Path, date: datetime) -> WriteResult:
    """Write EXIF dates to PNG/WEBP/GIF using Pillow."""
    img = Image.open(file_path)

    # Build EXIF data
    exif_data = img.getexif()
    date_str = date.strftime(EXIF_DATE_FORMAT)
    # IFD tags: DateTime (306), DateTimeOriginal (36867), DateTimeDigitized (36868)
    exif_data[306] = date_str
    exif_ifd = exif_data.get_ifd(piexif.ExifIFD.DateTimeOriginal)
    exif_ifd[piexif.ExifIFD.DateTimeOriginal] = date_str
    exif_ifd[piexif.ExifIFD.DateTimeDigitized] = date_str

    img.save(file_path, exif=exif_data.tobytes())
    img.close()

    return WriteResult(success=True, file_path=file_path)


def _write_video(file_path: Path, date: datetime) -> WriteResult:
    """Write creation date to MP4/MOV using mutagen."""
    # QuickTime uses UTC timestamps in ISO format
    utc_date = date.replace(tzinfo=timezone.utc)
    date_str = utc_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    video = MP4(str(file_path))
    # ©day is the QuickTime/iTunes date tag
    video["\xa9day"] = [date_str]
    video.save()

    return WriteResult(success=True, file_path=file_path)
