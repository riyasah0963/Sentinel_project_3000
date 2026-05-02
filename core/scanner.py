"""
scanner.py – Recursive directory/file scanner for Sentinel.

Walks a directory tree using os.walk() and computes SHA-256 hashes
for every accessible file.  Paths are stored relative to the root of
the monitored directory so that baselines remain valid even if the
monitored directory is relocated.

Design notes:
  - Relative paths are used as keys so baselines are portable.
  - Files that cannot be read (PermissionError, IOError) are skipped
    and counted; the caller receives a summary of skipped files.
  - Verbose mode prints each file as it is processed, useful for auditing
    large directories.
"""

import os
import logging
from core.hasher import compute_sha256

logger = logging.getLogger(__name__)


def scan_directory(root_path: str, verbose: bool = False) -> dict:
    """
    Scan *root_path* recursively and return a dict of relative paths → hashes.

    Args:
        root_path (str): The directory (or single file) to scan.
        verbose (bool):  If True, print each file path as it is processed.

    Returns:
        dict: {
            "files":   {relative_path: sha256_hex, ...},
            "skipped": [relative_path, ...]   # files that could not be read
        }

    Raises:
        ValueError: If *root_path* does not exist.

    Example:
        >>> result = scan_directory("./myproject")
        >>> isinstance(result["files"], dict)
        True
    """
    abs_root = os.path.abspath(root_path)

    if not os.path.exists(abs_root):
        raise ValueError(f"Path does not exist: {abs_root}")

    files_map: dict[str, str] = {}
    skipped: list[str] = []

    # Handle the case where a single file is passed
    if os.path.isfile(abs_root):
        digest = compute_sha256(abs_root)
        rel = os.path.basename(abs_root)
        if digest:
            files_map[rel] = digest
            if verbose:
                print(f"  [HASHED]  {rel}")
        else:
            skipped.append(rel)
            if verbose:
                print(f"  [SKIPPED] {rel}")
        return {"files": files_map, "skipped": skipped}

    # Recursive walk for directories
    for dir_root, _dirs, file_names in os.walk(abs_root):
        _dirs.sort()                               # sort subdirs for deterministic traversal order
        for fname in sorted(file_names):           # sorted for deterministic output
            full_path = os.path.join(dir_root, fname)
            rel_path = os.path.relpath(full_path, abs_root)

            digest = compute_sha256(full_path)
            if digest:
                files_map[rel_path] = digest
                if verbose:
                    print(f"  [HASHED]  {rel_path}")
            else:
                skipped.append(rel_path)
                if verbose:
                    print(f"  [SKIPPED] {rel_path}")

    logger.debug("Scanned %d files, skipped %d.", len(files_map), len(skipped))
    return {"files": files_map, "skipped": skipped}
