"""
test_baseline.py – Unit tests for core/baseline.py

Tests cover:
  - create_baseline() writes a valid JSON file.
  - Baseline JSON contains all required top-level keys.
  - 'files' dict in baseline contains correct relative paths.
  - create_baseline() returns False for a non-existent path.
  - load_baseline() returns None for a missing file.
  - load_baseline() returns None for a malformed JSON file.
  - load_baseline() returns None when required keys are absent.
  - Baseline can be loaded and its 'files' dict accessed correctly.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.baseline import create_baseline, load_baseline


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestCreateBaseline:

    def test_creates_json_file(self, tmp_path):
        """create_baseline() writes a JSON file to the given path."""
        src = tmp_path / "project"
        src.mkdir()
        (src / "main.py").write_text("print('hello')")
        out = tmp_path / "baseline.json"
        result = create_baseline(str(src), str(out))
        assert result is True
        assert out.exists()

    def test_json_has_required_keys(self, tmp_path):
        """Created baseline JSON contains all required top-level keys."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.txt").write_text("a")
        out = tmp_path / "baseline.json"
        create_baseline(str(src), str(out))
        data = json.loads(out.read_text())
        for key in ("sentinel_version", "created_at", "base_path", "files"):
            assert key in data, f"Missing key: {key}"

    def test_files_dict_contains_relative_paths(self, tmp_path):
        """The 'files' dict uses relative paths as keys."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "config.yaml").write_text("key: value")
        out = tmp_path / "baseline.json"
        create_baseline(str(src), str(out))
        data = json.loads(out.read_text())
        keys = list(data["files"].keys())
        assert "config.yaml" in keys
        assert not any(os.path.isabs(k) for k in keys)

    def test_files_dict_contains_sha256_and_size(self, tmp_path):
        """Each file entry has 'sha256' and 'size_bytes' fields."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "x.txt").write_bytes(b"hello")
        out = tmp_path / "b.json"
        create_baseline(str(src), str(out))
        data = json.loads(out.read_text())
        entry = data["files"]["x.txt"]
        assert "sha256" in entry
        assert "size_bytes" in entry
        assert entry["size_bytes"] == 5

    def test_returns_false_for_missing_path(self, tmp_path):
        """Returns False if the source path does not exist."""
        out = tmp_path / "baseline.json"
        result = create_baseline("/does/not/exist/12345", str(out))
        assert result is False

    def test_empty_directory_baseline(self, tmp_path):
        """Baseline for an empty directory has an empty 'files' dict."""
        src = tmp_path / "empty"
        src.mkdir()
        out = tmp_path / "b.json"
        create_baseline(str(src), str(out))
        data = json.loads(out.read_text())
        assert data["files"] == {}

    def test_verbose_mode_returns_true(self, tmp_path):
        """create_baseline() with verbose=True still returns True and writes the file."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "file.py").write_text("x = 1")
        out = tmp_path / "b.json"
        result = create_baseline(str(src), str(out), verbose=True)
        assert result is True
        assert out.exists()

    def test_skipped_files_recorded_in_metadata(self, tmp_path):
        """When all files are readable, skipped_files list in baseline is empty."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.txt").write_text("hello")
        out = tmp_path / "b.json"
        create_baseline(str(src), str(out))
        data = json.loads(out.read_text())
        assert "skipped_files" in data
        assert isinstance(data["skipped_files"], list)

    def test_elapsed_seconds_in_baseline(self, tmp_path):
        """Baseline includes elapsed_seconds metadata key."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "f.py").write_text("pass")
        out = tmp_path / "b.json"
        create_baseline(str(src), str(out))
        data = json.loads(out.read_text())
        assert "elapsed_seconds" in data
        assert isinstance(data["elapsed_seconds"], float)


class TestLoadBaseline:

    def test_loads_valid_baseline(self, tmp_path):
        """load_baseline() returns a dict for a valid baseline file."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "f.txt").write_text("x")
        out = tmp_path / "b.json"
        create_baseline(str(src), str(out))
        data = load_baseline(str(out))
        assert isinstance(data, dict)
        assert "files" in data

    def test_returns_none_for_missing_file(self, tmp_path):
        """Returns None when the baseline file does not exist."""
        result = load_baseline(str(tmp_path / "nonexistent.json"))
        assert result is None

    def test_returns_none_for_invalid_json(self, tmp_path):
        """Returns None when the file contains malformed JSON."""
        bad = tmp_path / "bad.json"
        bad.write_text("{ this is not valid json }")
        result = load_baseline(str(bad))
        assert result is None

    def test_returns_none_for_missing_required_keys(self, tmp_path):
        """Returns None when required keys are missing from the JSON."""
        incomplete = tmp_path / "incomplete.json"
        incomplete.write_text(json.dumps({"only_one_key": True}))
        result = load_baseline(str(incomplete))
        assert result is None
