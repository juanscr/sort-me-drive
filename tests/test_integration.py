"""Integration test with mock directory structure."""

from datetime import datetime
from pathlib import Path

import piexif
from PIL import Image

from sort_me_drive.cli import main


def _create_jpeg(path: Path, with_date: bool = False) -> None:
    """Create a minimal JPEG file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1, 1), color="red")
    img.save(str(path), "JPEG")

    if with_date:
        exif_data = piexif.load(str(path))
        exif_data["Exif"][piexif.ExifIFD.DateTimeOriginal] = b"2025:01:01 12:00:00"
        exif_bytes = piexif.dump(exif_data)
        piexif.insert(exif_bytes, str(path))


class TestIntegration:
    def _setup_tree(self, tmp_path: Path) -> None:
        """Create a realistic directory structure."""
        # WhatsApp photo — should get day from filename
        _create_jpeg(tmp_path / "2022" / "06" / "IMG-20220604-WA0020.jpg")
        # Mismatched filename date — should fallback to folder
        _create_jpeg(tmp_path / "2021" / "11" / "IMG-20190622-WA0003.jpg")
        # Snapchat — no date in filename, fallback
        _create_jpeg(tmp_path / "2020" / "01" / "Snapchat-1665498557.jpg")
        # Samsung camera — already has EXIF date
        _create_jpeg(tmp_path / "2025" / "01" / "20250101_120252.jpg", with_date=True)

    def test_dry_run(self, tmp_path: Path):
        self._setup_tree(tmp_path)
        exit_code = main(["--dry-run", "--verbose", str(tmp_path)])
        assert exit_code == 0

        # Verify no files were actually modified
        exif = piexif.load(str(tmp_path / "2022" / "06" / "IMG-20220604-WA0020.jpg"))
        assert piexif.ExifIFD.DateTimeOriginal not in exif.get("Exif", {})

    def test_apply_fixes(self, tmp_path: Path):
        self._setup_tree(tmp_path)
        exit_code = main(["--verbose", str(tmp_path)])
        assert exit_code == 0

        # WhatsApp: day from filename, folder month matches
        exif = piexif.load(str(tmp_path / "2022" / "06" / "IMG-20220604-WA0020.jpg"))
        assert exif["Exif"][piexif.ExifIFD.DateTimeOriginal] == b"2022:06:04 00:00:00"

        # Mismatched: folder fallback to first of month
        exif = piexif.load(str(tmp_path / "2021" / "11" / "IMG-20190622-WA0003.jpg"))
        assert exif["Exif"][piexif.ExifIFD.DateTimeOriginal] == b"2021:11:01 00:00:00"

        # Snapchat: folder fallback
        exif = piexif.load(str(tmp_path / "2020" / "01" / "Snapchat-1665498557.jpg"))
        assert exif["Exif"][piexif.ExifIFD.DateTimeOriginal] == b"2020:01:01 00:00:00"

        # Samsung: untouched (already had date)
        exif = piexif.load(str(tmp_path / "2025" / "01" / "20250101_120252.jpg"))
        assert exif["Exif"][piexif.ExifIFD.DateTimeOriginal] == b"2025:01:01 12:00:00"

    def test_nonexistent_directory(self):
        exit_code = main(["/nonexistent/path"])
        assert exit_code == 1
