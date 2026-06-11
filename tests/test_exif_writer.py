"""Tests for exif_writer module."""

from datetime import datetime
from pathlib import Path

import piexif
from PIL import Image
from mutagen.mp4 import MP4

from sort_me_drive.exif_writer import format_exif_date, write_exif_dates


def _create_jpeg(path: Path) -> None:
    """Create a minimal JPEG file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1, 1), color="red")
    img.save(str(path), "JPEG")


def _create_png(path: Path) -> None:
    """Create a minimal PNG file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1, 1), color="red")
    img.save(str(path), "PNG")


class TestFormatExifDate:
    def test_format(self):
        dt = datetime(2022, 6, 4, 15, 30, 45)
        assert format_exif_date(dt) == b"2022:06:04 15:30:45"

    def test_midnight(self):
        dt = datetime(2020, 1, 1, 0, 0, 0)
        assert format_exif_date(dt) == b"2020:01:01 00:00:00"


class TestWriteExifDates:
    def test_writes_dates_jpeg(self, tmp_path: Path):
        f = tmp_path / "photo.jpg"
        _create_jpeg(f)
        dt = datetime(2022, 6, 4, 15, 30, 0)

        result = write_exif_dates(f, dt)
        assert result.success is True

        exif_data = piexif.load(str(f))
        assert exif_data["Exif"][piexif.ExifIFD.DateTimeOriginal] == b"2022:06:04 15:30:00"
        assert exif_data["Exif"][piexif.ExifIFD.DateTimeDigitized] == b"2022:06:04 15:30:00"
        assert exif_data["0th"][piexif.ImageIFD.DateTime] == b"2022:06:04 15:30:00"

    def test_writes_dates_png(self, tmp_path: Path):
        f = tmp_path / "photo.png"
        _create_png(f)
        dt = datetime(2022, 6, 4, 15, 30, 0)

        result = write_exif_dates(f, dt)
        assert result.success is True

        # Verify via Pillow
        img = Image.open(f)
        exif = img.getexif()
        assert exif[306] == "2022:06:04 15:30:00"
        img.close()

    def test_dry_run_does_not_modify(self, tmp_path: Path):
        f = tmp_path / "photo.jpg"
        _create_jpeg(f)
        dt = datetime(2022, 6, 4, 15, 30, 0)

        result = write_exif_dates(f, dt, dry_run=True)
        assert result.success is True

        exif_data = piexif.load(str(f))
        assert piexif.ExifIFD.DateTimeOriginal not in exif_data.get("Exif", {})

    def test_creates_backup(self, tmp_path: Path):
        f = tmp_path / "photo.jpg"
        _create_jpeg(f)
        dt = datetime(2022, 6, 4, 15, 30, 0)

        result = write_exif_dates(f, dt, backup=True)
        assert result.success is True
        assert (tmp_path / "photo.jpg.bak").exists()

    def test_invalid_file(self, tmp_path: Path):
        f = tmp_path / "bad.jpg"
        f.write_text("not a jpeg")
        dt = datetime(2022, 6, 4, 15, 30, 0)

        result = write_exif_dates(f, dt)
        assert result.success is False
        assert result.error is not None

    def test_unsupported_extension(self, tmp_path: Path):
        f = tmp_path / "file.heic"
        f.write_bytes(b"\x00")
        dt = datetime(2022, 6, 4, 15, 30, 0)

        result = write_exif_dates(f, dt)
        assert result.success is False
        assert "unsupported" in result.error
