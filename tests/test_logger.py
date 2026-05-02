"""
test_logger.py – Unit tests for core/logger.py

Tests cover:
  - configure_logging() sets DEBUG level in verbose mode.
  - configure_logging() sets WARNING level in non-verbose mode.
  - save_report() writes a valid JSON file to an explicit path.
  - save_report() auto-generates a timestamped filename when given a directory.
  - save_report() returns False and does not raise when the path is unwritable.
"""

import json
import logging
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.logger import configure_logging, save_report


class TestConfigureLogging:

    def test_verbose_sets_debug_level(self):
        """configure_logging(verbose=True) sets the root logger to DEBUG."""
        configure_logging(verbose=True)
        assert logging.getLogger().level == logging.DEBUG

    def test_non_verbose_sets_warning_level(self):
        """configure_logging(verbose=False) sets the root logger to WARNING."""
        configure_logging(verbose=False)
        assert logging.getLogger().level == logging.WARNING

    def test_called_twice_does_not_raise(self):
        """Calling configure_logging() multiple times is safe (idempotent)."""
        configure_logging(verbose=False)
        configure_logging(verbose=True)
        configure_logging(verbose=False)


class TestSaveReport:

    def test_saves_to_explicit_path(self, tmp_path):
        """save_report() writes a JSON file to the given explicit file path."""
        report = {"summary": {"added": 1}, "checked_at": "2026-01-01"}
        out = tmp_path / "report.json"
        result = save_report(report, str(out))
        assert result is True
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["summary"]["added"] == 1

    def test_saves_to_directory_auto_filename(self, tmp_path):
        """When given a directory, save_report() creates a timestamped file inside it."""
        report = {"summary": {"deleted": 0}}
        result = save_report(report, str(tmp_path))
        assert result is True
        json_files = list(tmp_path.glob("sentinel_report_*.json"))
        assert len(json_files) == 1
        data = json.loads(json_files[0].read_text())
        assert data["summary"]["deleted"] == 0

    def test_creates_parent_directories(self, tmp_path):
        """save_report() creates intermediate directories if they don't exist."""
        report = {"info": "test"}
        nested = tmp_path / "deep" / "nested" / "report.json"
        result = save_report(report, str(nested))
        assert result is True
        assert nested.exists()

    def test_returns_false_on_write_failure(self, tmp_path):
        """save_report() returns False when the file cannot be written."""
        from unittest.mock import patch
        report = {"x": 1}
        out = tmp_path / "report.json"
        with patch("builtins.open", side_effect=IOError("simulated disk full")):
            result = save_report(report, str(out))
        assert result is False

    def test_report_json_is_valid(self, tmp_path):
        """The saved file is valid JSON with correct content."""
        report = {"sentinel_version": "1.0.0", "added": ["file.txt"]}
        out = tmp_path / "r.json"
        save_report(report, str(out))
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["sentinel_version"] == "1.0.0"
        assert data["added"] == ["file.txt"]
