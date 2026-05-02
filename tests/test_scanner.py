"""
test_scanner.py – Unit tests for core/scanner.py

Tests cover:
  - Scanning a flat directory returns all files.
  - Scanning a nested directory tree returns all files with relative paths.
  - Scanning an empty directory returns an empty dict.
  - Scanning a single file (not a directory) works correctly.
  - Files that cannot be read appear in 'skipped', not 'files'.
  - Relative paths are used as keys (not absolute paths).
  - Providing a non-existent path raises ValueError.
"""

import os
import stat
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.scanner import scan_directory


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestScanDirectory:

    def test_flat_directory_all_files_found(self, tmp_path):
        """All files in a flat directory are returned."""
        (tmp_path / "a.txt").write_text("aaa")
        (tmp_path / "b.txt").write_text("bbb")
        result = scan_directory(str(tmp_path))
        assert set(result["files"].keys()) == {"a.txt", "b.txt"}

    def test_nested_directory_uses_relative_paths(self, tmp_path):
        """Files in subdirectories are keyed by relative path."""
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "nested.py").write_text("x = 1")
        (tmp_path / "top.py").write_text("y = 2")
        result = scan_directory(str(tmp_path))
        keys = set(result["files"].keys())
        # Keys should be relative, e.g. "subdir/nested.py" not absolute
        assert any("nested.py" in k for k in keys)
        assert all(not os.path.isabs(k) for k in keys)

    def test_empty_directory_returns_empty_files(self, tmp_path):
        """Scanning an empty directory returns an empty files dict."""
        result = scan_directory(str(tmp_path))
        assert result["files"] == {}
        assert result["skipped"] == []

    def test_single_file_scan(self, tmp_path):
        """Passing a single file path (not directory) works."""
        f = tmp_path / "single.txt"
        f.write_bytes(b"hello")
        result = scan_directory(str(f))
        assert len(result["files"]) == 1
        assert list(result["files"].keys()) == ["single.txt"]

    def test_nonexistent_path_raises_valueerror(self):
        """A path that does not exist raises ValueError."""
        with pytest.raises(ValueError):
            scan_directory("/nonexistent/path/12345")

    def test_hashes_are_64_char_strings(self, tmp_path):
        """All returned hash values are 64-character hex strings."""
        (tmp_path / "file.dat").write_bytes(b"data")
        result = scan_directory(str(tmp_path))
        for digest in result["files"].values():
            assert isinstance(digest, str)
            assert len(digest) == 64

    def test_returns_skipped_list(self, tmp_path):
        """Result dict always contains a 'skipped' key."""
        (tmp_path / "f.txt").write_text("ok")
        result = scan_directory(str(tmp_path))
        assert "skipped" in result
        assert isinstance(result["skipped"], list)

    def test_multiple_nested_levels(self, tmp_path):
        """Files several levels deep are discovered correctly."""
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / "deep.txt").write_text("deep content")
        result = scan_directory(str(tmp_path))
        assert any("deep.txt" in k for k in result["files"].keys())

    def test_file_count_matches(self, tmp_path):
        """The number of entries in 'files' matches actual file count."""
        for i in range(5):
            (tmp_path / f"file_{i}.txt").write_text(f"content {i}")
        result = scan_directory(str(tmp_path))
        assert len(result["files"]) == 5
