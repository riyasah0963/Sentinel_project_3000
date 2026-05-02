"""
checker.py – Integrity comparison engine for Sentinel.

Loads a stored baseline, re-scans the monitored directory, and
computes the symmetric difference to categorise every change as:
    ADDED    – file present now but not in baseline
    DELETED  – file in baseline but no longer on disk
    MODIFIED – file present in both but SHA-256 hash has changed
    UNCHANGED– file present in both with identical hash (not printed
               unless --verbose)

Results are displayed with ANSI colour coding (green/red/amber) in
terminals that support it, and optionally saved as a timestamped JSON
report file for archival or SIEM integration.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone

from core.baseline import load_baseline, SENTINEL_VERSION
from core.scanner import scan_directory
from core.logger import save_report
from core.utils import (
    colour, GREEN, RED, YELLOW, CYAN, RESET,
    print_success, print_error, print_info, print_warning,
)

logger = logging.getLogger(__name__)


def check_integrity(
    path: str,
    baseline_file: str,
    verbose: bool = False,
    report_file: str | None = None,
) -> bool:
    """
    Compare the current state of *path* against the stored baseline.

    Args:
        path (str):           Directory (or file) to check.
        baseline_file (str):  Path to the JSON baseline created by --init.
        verbose (bool):       If True, also list unchanged files.
        report_file (str):    Optional path to save a JSON report.

    Returns:
        bool: True if the check completed (regardless of changes found),
              False if a fatal error prevented completion.

    Side-effects:
        Prints a colour-coded report to stdout.
        If *report_file* is given, writes a JSON report to that path.
    """
    # ── Load baseline ────────────────────────────────────────────────────────
    baseline_data = load_baseline(baseline_file)
    if baseline_data is None:
        return False

    baseline_files: dict[str, dict] = baseline_data["files"]
    stored_path: str = baseline_data.get("base_path", path)
    created_at: str = baseline_data.get("created_at", "unknown")

    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        print_error(f"Path not found: {abs_path}")
        return False

    print_info(f"Checking integrity of : {abs_path}")
    print_info(f"Baseline created at   : {created_at}")
    print_info(f"Baseline stored path  : {stored_path}")
    if verbose:
        print_info("Verbose mode – all files will be listed.\n")

    # ── Scan current state ───────────────────────────────────────────────────
    start = time.perf_counter()
    try:
        scan_result = scan_directory(abs_path, verbose=False)
    except ValueError as exc:
        print_error(str(exc))
        return False

    elapsed = time.perf_counter() - start
    current_files: dict[str, str] = scan_result["files"]
    scan_skipped: list[str] = scan_result["skipped"]

    # Build a simple hash-only view of the baseline for comparison
    baseline_hashes: dict[str, str] = {
        rel: meta.get("sha256", "") for rel, meta in baseline_files.items()
    }

    baseline_set = set(baseline_hashes.keys())
    current_set = set(current_files.keys())

    added    = sorted(current_set - baseline_set)
    deleted  = sorted(baseline_set - current_set)
    both     = baseline_set & current_set
    modified = sorted(f for f in both if baseline_hashes[f] != current_files[f])
    unchanged = sorted(f for f in both if baseline_hashes[f] == current_files[f])

    # ── Print results ────────────────────────────────────────────────────────
    separator = "─" * 60
    print(f"\n{CYAN}{separator}{RESET}")
    print(f"{CYAN}  Sentinel Integrity Report{RESET}")
    print(f"{CYAN}{separator}{RESET}\n")

    if added:
        print(f"{GREEN}  ADDED ({len(added)} file(s)){RESET}")
        for f in added:
            print(f"  {GREEN}  ✔  [ADDED]    {f}{RESET}")
        print()

    if deleted:
        print(f"{RED}  DELETED ({len(deleted)} file(s)){RESET}")
        for f in deleted:
            print(f"  {RED}  ✖  [DELETED]  {f}{RESET}")
        print()

    if modified:
        print(f"{YELLOW}  MODIFIED ({len(modified)} file(s)){RESET}")
        for f in modified:
            old_hash = baseline_hashes[f]
            new_hash = current_files[f]
            print(f"  {YELLOW}  ⚠  [MODIFIED] {f}{RESET}")
            print(f"       Baseline SHA-256 : {old_hash}")
            print(f"       Current  SHA-256 : {new_hash}")
        print()

    if verbose and unchanged:
        print(f"  UNCHANGED ({len(unchanged)} file(s))")
        for f in unchanged:
            print(f"    ✓  [OK]       {f}")
        print()

    if scan_skipped:
        print_warning(f"  {len(scan_skipped)} file(s) could not be read and were skipped.")
        for s in scan_skipped:
            print(f"  {YELLOW}  ⚠  [SKIPPED]  {s}{RESET}")
        print()

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"{CYAN}{separator}{RESET}")
    total_changes = len(added) + len(deleted) + len(modified)
    if total_changes == 0:
        print_success("No changes detected. All files match the baseline.")
    else:
        print(
            f"  Summary: "
            f"{GREEN}{len(added)} added{RESET}  "
            f"{RED}{len(deleted)} deleted{RESET}  "
            f"{YELLOW}{len(modified)} modified{RESET}  "
            f"{len(unchanged)} unchanged"
        )
    print(f"  Scan completed in {elapsed:.3f}s")
    print(f"{CYAN}{separator}{RESET}\n")

    # ── Optional JSON report ─────────────────────────────────────────────────
    if report_file:
        report = {
            "sentinel_version": SENTINEL_VERSION,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "base_path": abs_path,
            "baseline_file": os.path.abspath(baseline_file),
            "baseline_created_at": created_at,
            "elapsed_seconds": round(elapsed, 3),
            "summary": {
                "added": len(added),
                "deleted": len(deleted),
                "modified": len(modified),
                "unchanged": len(unchanged),
                "skipped": len(scan_skipped),
            },
            "added": added,
            "deleted": deleted,
            "modified": [
                {
                    "path": f,
                    "baseline_sha256": baseline_hashes[f],
                    "current_sha256": current_files[f],
                }
                for f in modified
            ],
            "skipped": scan_skipped,
        }
        save_report(report, report_file)

    return True
