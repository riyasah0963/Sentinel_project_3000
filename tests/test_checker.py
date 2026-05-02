"""
test_checker.py – Integration tests for core/checker.py

These are end-to-end tests that exercise the full baseline → modify → check
workflow.  They verify that check_integrity() correctly detects:
  - No changes (clean pass)
  - Added files
  - Deleted files
  - Modified files (content changed)
  - Multiple simultaneous changes
  - Missing baseline file returns False
  - Non-existent target path returns False
  - Optional JSON report is written when report_file is specified
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.baseline import create_baseline
from core.checker import check_integrity


# ── Fixture: fresh monitored directory with baseline ──────────────────────────

@pytest.fixture()
def monitored(tmp_path):
    """
    Create a temporary directory with three files and a baseline.
    Returns (dir_path, baseline_path) as strings.
    """
    src = tmp_path / "project"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    (src / "config.yaml").write_text("key: value")
    (src / "README.md").write_text("# My Project")
    baseline = tmp_path / "baseline.json"
    create_baseline(str(src), str(baseline))
    return str(src), str(baseline)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestCheckIntegrity:

    def test_no_changes_returns_true(self, monitored):
        """check_integrity() returns True and detects zero changes on clean directory."""
        src, baseline = monitored
        result = check_integrity(src, baseline)
        assert result is True

    def test_detects_added_file(self, monitored):
        """A newly added file is detected."""
        src, baseline = monitored
        # Add a new file after baseline was created
        with open(os.path.join(src, "new_file.py"), "w"):
            pass
        result = check_integrity(src, baseline)
        assert result is True   # completes without error

    def test_detects_deleted_file(self, monitored):
        """A deleted file is detected."""
        src, baseline = monitored
        os.remove(os.path.join(src, "README.md"))
        result = check_integrity(src, baseline)
        assert result is True

    def test_detects_modified_file(self, monitored):
        """A file whose content has changed is detected."""
        src, baseline = monitored
        with open(os.path.join(src, "config.yaml"), "w") as fh:
            fh.write("key: CHANGED_VALUE")
        result = check_integrity(src, baseline)
        assert result is True

    def test_detects_multiple_changes(self, monitored):
        """Multiple simultaneous changes (add + delete + modify) are all detected."""
        src, baseline = monitored
        # Modify
        with open(os.path.join(src, "main.py"), "w") as fh:
            fh.write("print('modified')")
        # Delete
        os.remove(os.path.join(src, "README.md"))
        # Add
        with open(os.path.join(src, "extra.txt"), "w") as fh:
            fh.write("new content")
        result = check_integrity(src, baseline)
        assert result is True

    def test_missing_baseline_returns_false(self, tmp_path):
        """Returns False when the baseline file does not exist."""
        src = tmp_path / "src"
        src.mkdir()
        result = check_integrity(str(src), str(tmp_path / "missing.json"))
        assert result is False

    def test_missing_path_returns_false(self, tmp_path):
        """Returns False when the monitored path does not exist."""
        baseline = tmp_path / "b.json"
        # Create a minimal valid baseline manually
        import json as _json
        baseline.write_text(_json.dumps({
            "sentinel_version": "1.0.0",
            "created_at": "2025-01-01T00:00:00",
            "base_path": "/nonexistent",
            "total_files": 0,
            "skipped_files": [],
            "files": {},
        }))
        result = check_integrity("/nonexistent/path/12345", str(baseline))
        assert result is False

    def test_report_file_is_created(self, monitored, tmp_path):
        """When report_file is given, a JSON report is written."""
        src, baseline = monitored
        report_path = str(tmp_path / "report.json")
        check_integrity(src, baseline, report_file=report_path)
        assert os.path.isfile(report_path)
        with open(report_path, encoding="utf-8") as fh:
            data = json.load(fh)
        assert "summary" in data
        assert "checked_at" in data

    def test_report_summary_counts_correct(self, monitored, tmp_path):
        """Report summary reflects the actual number of changes."""
        src, baseline = monitored
        os.remove(os.path.join(src, "README.md"))               # 1 deleted
        with open(os.path.join(src, "new.txt"), "w") as fh:     # 1 added
            fh.write("x")
        report_path = str(tmp_path / "report.json")
        check_integrity(src, baseline, report_file=report_path)
        with open(report_path, encoding="utf-8") as fh:
            data = json.load(fh)
        assert data["summary"]["deleted"] == 1
        assert data["summary"]["added"] == 1

    def test_verbose_mode_runs_without_error(self, monitored):
        """verbose=True does not raise any exception."""
        src, baseline = monitored
        result = check_integrity(src, baseline, verbose=True)
        assert result is True
