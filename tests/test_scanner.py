"""Tests for scanner module."""

from pathlib import Path

import piexif
from PIL import Image

from sort_me_drive.scanner import has_exif_date, scan_directory


def _create_jpeg(path: Path, with_date: bool = False) -> None:
    """Create a minimal JPEG file, optionally with DateTimeOriginal."""
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1, 1), color="red")
    img.save(str(path), "JPEG")

    if with_date:
        exif_data = piexif.load(str(path))
        exif_data["Exif"][piexif.ExifIFD.DateTimeOriginal] = b"2025:01:01 12:00:00"
        exif_bytes = piexif.dump(exif_data)
        piexif.insert(exif_bytes, str(path))


class TestHasExifDate:
    def test_with_date(self, tmp_path: Path):
        f = tmp_path / "photo.jpg"
        _create_jpeg(f, with_date=True)
        assert has_exif_date(f) is True

    def test_without_date(self, tmp_path: Path):
        f = tmp_path / "photo.jpg"
        _create_jpeg(f, with_date=False)
        assert has_exif_date(f) is False

    def test_nonexistent_file(self, tmp_path: Path):
        assert has_exif_date(tmp_path / "nope.jpg") is False

    def test_invalid_file(self, tmp_path: Path):
        f = tmp_path / "bad.jpg"
        f.write_text("not a jpeg")
        assert has_exif_date(f) is False


class TestScanDirectory:
    def test_finds_files_to_process(self, tmp_path: Path):
        (tmp_path / "2022" / "06").mkdir(parents=True)
        _create_jpeg(tmp_path / "2022" / "06" / "photo1.jpg", with_date=False)
        _create_jpeg(tmp_path / "2022" / "06" / "photo2.jpg", with_date=True)

        result = scan_directory(tmp_path)
        assert result.total_files == 2
        assert len(result.to_process) == 1
        assert len(result.skipped_has_date) == 1

    def test_filters_by_extension(self, tmp_path: Path):
        _create_jpeg(tmp_path / "photo.jpg")
        (tmp_path / "doc.txt").write_text("hello")

        result = scan_directory(tmp_path, extensions={"jpg"})
        assert result.total_files == 1

    def test_empty_directory(self, tmp_path: Path):
        result = scan_directory(tmp_path)
        assert result.total_files == 0

    def test_nonexistent_directory(self):
        result = scan_directory(Path("/nonexistent"))
        assert result.total_files == 0
