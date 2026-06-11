"""File discovery and filtering."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import piexif
from mutagen.mp4 import MP4

DEFAULT_EXTENSIONS = {"jpg", "jpeg", "png", "heic", "mp4", "mov", "gif", "webp"}

VIDEO_EXTENSIONS = {".mp4", ".mov"}


@dataclass
class ScanResult:
    """Results of scanning a directory."""

    to_process: list[Path] = field(default_factory=list)
    skipped_has_date: list[Path] = field(default_factory=list)
    total_files: int = 0


def has_exif_date(file_path: Path) -> bool:
    """Check if a file already has date metadata set."""
    ext = file_path.suffix.lower()

    if ext in VIDEO_EXTENSIONS:
        return _video_has_date(file_path)

    # Image files: check EXIF DateTimeOriginal
    try:
        exif_data = piexif.load(str(file_path))
        exif_ifd = exif_data.get("Exif", {})
        date_original = exif_ifd.get(piexif.ExifIFD.DateTimeOriginal)
        return date_original is not None and date_original != b""
    except Exception:
        return False


def _video_has_date(file_path: Path) -> bool:
    """Check if a video file already has a creation date tag."""
    try:
        video = MP4(str(file_path))
        day_tag = video.get("\xa9day")
        return day_tag is not None and len(day_tag) > 0 and day_tag[0] != ""
    except Exception:
        return False


def scan_directory(
    directory: Path,
    extensions: set[str] | None = None,
) -> ScanResult:
    """Recursively scan a directory for image/video files.

    Files that already have DateTimeOriginal are placed in skipped_has_date.
    Files without it are placed in to_process.
    """
    if extensions is None:
        extensions = DEFAULT_EXTENSIONS

    # Normalize extensions to lowercase without dots
    extensions = {ext.lower().lstrip(".") for ext in extensions}

    result = ScanResult()

    if not directory.is_dir():
        return result

    for file_path in sorted(directory.rglob("*")):
        if not file_path.is_file():
            continue

        ext = file_path.suffix.lower().lstrip(".")
        if ext not in extensions:
            continue

        result.total_files += 1

        if has_exif_date(file_path):
            result.skipped_has_date.append(file_path)
        else:
            result.to_process.append(file_path)

    return result
