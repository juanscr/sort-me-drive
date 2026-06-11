"""Tests for date_resolver module."""

from datetime import datetime
from pathlib import Path

import pytest

from sort_me_drive.date_resolver import (
    extract_filename_date,
    extract_folder_date,
    resolve_date,
)


class TestExtractFolderDate:
    def test_simple_yyyy_mm(self):
        result = extract_folder_date(Path("/photos/2022/06/img.jpg"))
        assert result is not None
        assert result.year == 2022
        assert result.month == 6

    def test_nested_path(self):
        result = extract_folder_date(Path("/home/user/OneDrive/Samsung Gallery/DCIM/2021/11/photo.jpg"))
        assert result is not None
        assert result.year == 2021
        assert result.month == 11

    def test_last_occurrence_wins(self):
        result = extract_folder_date(Path("/backup/2020/01/restored/2023/03/img.jpg"))
        assert result is not None
        assert result.year == 2023
        assert result.month == 3

    def test_no_pattern(self):
        result = extract_folder_date(Path("/photos/random/img.jpg"))
        assert result is None

    def test_invalid_month(self):
        result = extract_folder_date(Path("/photos/2022/13/img.jpg"))
        assert result is None

    def test_month_zero(self):
        result = extract_folder_date(Path("/photos/2022/00/img.jpg"))
        assert result is None


class TestExtractFilenameDate:
    def test_whatsapp(self):
        result = extract_filename_date("IMG-20220604-WA0020.jpg")
        assert result is not None
        assert result.year == 2022
        assert result.month == 6
        assert result.day == 4
        assert result.has_time is False

    def test_samsung_timestamp(self):
        result = extract_filename_date("20250101_120252_HDR.jpg")
        assert result is not None
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 12
        assert result.minute == 2
        assert result.second == 52
        assert result.has_time is True

    def test_img_timestamp(self):
        result = extract_filename_date("IMG_20210315_093045.jpg")
        assert result is not None
        assert result.year == 2021
        assert result.month == 3
        assert result.day == 15
        assert result.has_time is True

    def test_vid_timestamp(self):
        result = extract_filename_date("VID_20200705_143022.mp4")
        assert result is not None
        assert result.year == 2020
        assert result.month == 7
        assert result.day == 5

    def test_snapchat(self):
        result = extract_filename_date("Snapchat-1665498557.jpg")
        assert result is None

    def test_received(self):
        result = extract_filename_date("received_1234567890.jpg")
        assert result is None

    def test_no_pattern(self):
        result = extract_filename_date("random_photo.jpg")
        assert result is None


class TestResolveDate:
    def test_filename_matches_folder(self):
        path = Path("/photos/2022/06/IMG-20220604-WA0020.jpg")
        result = resolve_date(path)
        assert result is not None
        assert result.date == datetime(2022, 6, 4, 0, 0, 0)
        assert result.source == "filename_day_only"

    def test_filename_with_time(self):
        path = Path("/photos/2025/01/20250101_120252.jpg")
        result = resolve_date(path)
        assert result is not None
        assert result.date == datetime(2025, 1, 1, 12, 2, 52)
        assert result.source == "filename"

    def test_filename_mismatch_falls_back(self):
        # Folder says 2021/11 but filename says 2019-06-22
        path = Path("/photos/2021/11/IMG-20190622-WA0003.jpg")
        result = resolve_date(path)
        assert result is not None
        assert result.date == datetime(2021, 11, 1, 0, 0, 0)
        assert result.source == "folder_fallback"

    def test_no_date_in_filename(self):
        path = Path("/photos/2020/01/Snapchat-1665498557.jpg")
        result = resolve_date(path)
        assert result is not None
        assert result.date == datetime(2020, 1, 1, 0, 0, 0)
        assert result.source == "folder_fallback"

    def test_no_folder_pattern(self):
        path = Path("/photos/orphan_photo.jpg")
        result = resolve_date(path)
        assert result is None

    def test_folder_year_month_preserved(self):
        path = Path("/photos/2023/08/IMG-20230815-WA0001.jpg")
        result = resolve_date(path)
        assert result is not None
        assert result.folder_year == 2023
        assert result.folder_month == 8
