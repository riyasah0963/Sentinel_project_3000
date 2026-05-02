"""
test_hasher.py – Unit tests for core/hasher.py

Tests cover:
  - Correct SHA-256 output against NIST-published test vectors.
  - Correct handling of empty files.
  - Graceful None return for non-existent files.
  - Graceful None return for permission-denied files.
  - Different content produces different hashes (avalanche effect).
  - Large file hashing (chunked reading) produces consistent results.
"""

import hashlib
import os
import stat
import sys
import tempfile

import pytest

# Add project root to path so tests can import core modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.hasher import compute_sha256, CHUNK_SIZE


# ── Helpers ──────────────────────────────────────────────────────────────────

def _sha256_of_bytes(data: bytes) -> str:
    """Return the expected SHA-256 hex digest of *data*."""
    return hashlib.sha256(data).hexdigest()


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestComputeSha256:

    def test_known_content(self, tmp_path):
        """SHA-256 of known content matches the expected digest."""
        content = b"Sentinel file integrity monitoring"
        expected = _sha256_of_bytes(content)
        f = tmp_path / "test.txt"
        f.write_bytes(content)
        assert compute_sha256(str(f)) == expected

    def test_empty_file(self, tmp_path):
        """SHA-256 of an empty file is the well-known empty-string digest."""
        # NIST test vector: SHA-256("") =
        #   e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        assert compute_sha256(str(f)) == expected

    def test_returns_none_for_missing_file(self):
        """Returns None when the file does not exist."""
        result = compute_sha256("/tmp/this_file_does_not_exist_sentinel_9999.txt")
        assert result is None

    def test_returns_64_hex_chars(self, tmp_path):
        """SHA-256 digest is exactly 64 lowercase hex characters."""
        f = tmp_path / "data.bin"
        f.write_bytes(b"hello world")
        digest = compute_sha256(str(f))
        assert digest is not None
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)

    def test_different_content_different_hash(self, tmp_path):
        """Two files with different content produce different digests."""
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_bytes(b"content A")
        f2.write_bytes(b"content B")
        assert compute_sha256(str(f1)) != compute_sha256(str(f2))

    def test_identical_content_identical_hash(self, tmp_path):
        """Two files with identical content produce identical digests."""
        f1 = tmp_path / "copy1.txt"
        f2 = tmp_path / "copy2.txt"
        data = b"identical content"
        f1.write_bytes(data)
        f2.write_bytes(data)
        assert compute_sha256(str(f1)) == compute_sha256(str(f2))

    def test_single_byte_change_changes_hash(self, tmp_path):
        """Changing even one byte produces a completely different hash (avalanche)."""
        f1 = tmp_path / "orig.bin"
        f2 = tmp_path / "changed.bin"
        data = bytearray(b"A" * 100)
        f1.write_bytes(bytes(data))
        data[50] = ord("B")          # flip exactly one byte
        f2.write_bytes(bytes(data))
        assert compute_sha256(str(f1)) != compute_sha256(str(f2))

    def test_large_file_chunked_reading(self, tmp_path):
        """Large file (> CHUNK_SIZE) is hashed correctly via chunked reading."""
        # Write a file 3× larger than CHUNK_SIZE
        large_data = b"X" * (CHUNK_SIZE * 3 + 1)
        f = tmp_path / "large.bin"
        f.write_bytes(large_data)
        expected = _sha256_of_bytes(large_data)
        assert compute_sha256(str(f)) == expected

    @pytest.mark.skipif(sys.platform == "win32", reason="chmod not reliable on Windows")
    def test_permission_denied_returns_none(self, tmp_path):
        """Returns None (not exception) when file cannot be read."""
        f = tmp_path / "protected.txt"
        f.write_bytes(b"secret")
        os.chmod(str(f), 0o000)       # remove all permissions
        try:
            result = compute_sha256(str(f))
            assert result is None
        finally:
            os.chmod(str(f), stat.S_IRUSR | stat.S_IWUSR)   # restore so tmp_path cleanup works
