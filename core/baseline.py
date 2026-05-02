"""
baseline.py – Baseline creation and JSON persistence for Sentinel.

A baseline is a JSON snapshot of a directory at a specific point in time.
It records file paths (relative to the monitored root), their SHA-256
hashes, file sizes, and metadata such as the creation timestamp and the
Sentinel version.

Schema example:
    {
        "sentinel_version": "1.0.0",
        "created_at": "2025-04-21T10:30:00.123456",
        "base_path": "/home/user/myproject",
        "total_files": 42,
        "skipped_files": [],
        "files": {
            "src/main.py": {
                "sha256": "a1b2c3...",
                "size_bytes": 1024
            },
            ...
        }
    }

The JSON file is written with 2-space indentation for human readability
and can be version-controlled alongside source code.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone

from core.scanner import scan_directory
from core.utils import (
    colour, GREEN, RED, YELLOW, RESET,
    print_success, print_error, print_info,
)

SENTINEL_VERSION = "1.0.0"
BASELINE_SCHEMA_VERSION = 1

logger = logging.getLogger(__name__)


def _get_file_size(root_path: str, rel_path: str) -> int:
    """
    Return the size in bytes of a file given the root directory and relative path.

    Args:
        root_path (str): Absolute path to the monitored root directory.
        rel_path (str):  Path of the file relative to *root_path*.

    Returns:
        int: File size in bytes, or 0 if the file cannot be stat-ed.
    """
    try:
        return os.path.getsize(os.path.join(root_path, rel_path))
    except OSError:
        return 0


def create_baseline(path: str, baseline_file: str, verbose: bool = False) -> bool:
    """
    Scan *path* and persist a baseline snapshot to *baseline_file*.

    Args:
        path (str):          Directory (or file) to monitor.
        baseline_file (str): Destination path for the JSON baseline.
        verbose (bool):      If True, print each file as it is hashed.

    Returns:
        bool: True on success, False if an error prevented completion.

    Side-effects:
        Writes a JSON file to *baseline_file*.
        Prints a summary to stdout.
    """
    abs_path = os.path.abspath(path)

    if not os.path.exists(abs_path):
        print_error(f"Path not found: {abs_path}")
        return False

    print_info(f"Creating baseline for: {abs_path}")
    if verbose:
        print_info("Verbose mode – listing all files:\n")

    start = time.perf_counter()

    try:
        scan_result = scan_directory(abs_path, verbose=verbose)
    except ValueError as exc:
        print_error(str(exc))
        return False

    elapsed = time.perf_counter() - start
    raw_files: dict[str, str] = scan_result["files"]
    skipped: list[str] = scan_result["skipped"]

    # Build enriched file records (hash + size)
    enriched: dict[str, dict] = {}
    for rel_path, digest in raw_files.items():
        enriched[rel_path] = {
            "sha256": digest,
            "size_bytes": _get_file_size(abs_path, rel_path),
        }

    baseline_data = {
        "sentinel_version": SENTINEL_VERSION,
        "schema_version": BASELINE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base_path": abs_path,
        "total_files": len(enriched),
        "skipped_files": skipped,
        "elapsed_seconds": round(elapsed, 3),
        "files": enriched,
    }

    # Ensure parent directory exists
    parent_dir = os.path.dirname(os.path.abspath(baseline_file))
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    try:
        with open(baseline_file, "w", encoding="utf-8") as fh:
            json.dump(baseline_data, fh, indent=2, sort_keys=True)
    except IOError as exc:
        print_error(f"Could not write baseline file: {exc}")
        return False

    print()
    print_success(
        f"Baseline created → {baseline_file}\n"
        f"  Files hashed : {len(enriched)}\n"
        f"  Files skipped: {len(skipped)}\n"
        f"  Time taken   : {elapsed:.3f}s"
    )
    if skipped:
        print(f"\n{YELLOW}  Skipped files (permission/read errors):{RESET}")
        for s in skipped:
            print(f"    {YELLOW}• {s}{RESET}")

    return True


def load_baseline(baseline_file: str) -> dict | None:
    """
    Load and validate a JSON baseline file.

    Args:
        baseline_file (str): Path to the baseline JSON file.

    Returns:
        dict | None: Parsed baseline dictionary, or None on failure.
    """
    if not os.path.isfile(baseline_file):
        print_error(f"Baseline file not found: {baseline_file}")
        return None

    try:
        with open(baseline_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        print_error(f"Baseline file contains invalid JSON: {exc}")
        return None
    except IOError as exc:
        print_error(f"Cannot read baseline file: {exc}")
        return None

    # Schema validation
    required_keys = {"files", "base_path", "created_at", "sentinel_version"}
    missing = required_keys - set(data.keys())
    if missing:
        print_error(
            f"Baseline file is missing required keys: {missing}\n"
            "The file may be corrupt or was created by a different tool."
        )
        return None

    return data
