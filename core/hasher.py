"""
hasher.py – SHA-256 cryptographic hash computation for Sentinel.

This module provides the core hashing functionality used throughout
Sentinel.  Files are read in configurable chunks to support arbitrarily
large files without exhausting system memory.

Key design decisions:
  - 65,536-byte (64 KB) chunks balance I/O throughput and memory usage.
  - Specific exceptions (IOError, PermissionError) are caught rather than
    a bare 'except', so unexpected errors still propagate correctly.
  - Returns None on failure so callers can skip unreadable files gracefully.
"""

import hashlib
import logging

# 64 KB chunks – empirically near-optimal for local SSD/HDD throughput.
CHUNK_SIZE = 65_536

logger = logging.getLogger(__name__)


def compute_sha256(file_path: str) -> str | None:
    """
    Compute the SHA-256 digest of a file by reading it in chunks.

    Args:
        file_path (str): Absolute or relative path to the file.

    Returns:
        str | None: Lowercase hex digest (64 characters) on success,
                    or None if the file cannot be read.

    Example:
        >>> digest = compute_sha256("/etc/hosts")
        >>> isinstance(digest, str) and len(digest) == 64
        True
    """
    hash_obj = hashlib.sha256()
    try:
        with open(file_path, "rb") as fh:
            while True:
                chunk = fh.read(CHUNK_SIZE)
                if not chunk:
                    break
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except PermissionError:
        logger.warning("Permission denied – skipping: %s", file_path)
        return None
    except IOError as exc:
        logger.warning("Could not read file (%s) – skipping: %s", exc, file_path)
        return None
