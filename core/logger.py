"""
logger.py – Report persistence and logging configuration for Sentinel.

This module handles two responsibilities:
  1. Configuring Python's standard logging framework so that all modules
     in Sentinel write consistent, timestamped log messages.
  2. Saving comparison reports as JSON files for archival, auditing, or
     integration with external tools.

Log levels:
    DEBUG   – fine-grained tracing (per-file hashing progress)
    INFO    – normal operational messages
    WARNING – skipped files, non-fatal issues
    ERROR   – failures that prevent an operation from completing
"""

import json
import logging
import os
from datetime import datetime


def configure_logging(verbose: bool = False) -> None:
    """
    Configure the root logger for Sentinel.

    In non-verbose mode only WARNING and above are shown.
    In verbose mode DEBUG messages are also shown.

    Args:
        verbose (bool): If True, set log level to DEBUG; otherwise WARNING.
    """
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s – %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # basicConfig is a no-op when handlers are already configured (e.g. pytest).
    # Explicitly set the root level so the call always takes effect.
    logging.getLogger().setLevel(level)


def save_report(report: dict, output_path: str) -> bool:
    """
    Serialise *report* to a JSON file at *output_path*.

    If *output_path* is a directory, a timestamped filename is generated
    automatically inside it.  Otherwise the path is used as-is.

    Args:
        report (dict):      The report dictionary to serialise.
        output_path (str):  File path (or directory) for the output JSON.

    Returns:
        bool: True on success, False if the file could not be written.

    Side-effects:
        Creates parent directories as needed.
        Prints the path of the saved report to stdout.
    """
    # Auto-generate filename if a directory is given
    if os.path.isdir(output_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_path, f"sentinel_report_{timestamp}.json")

    parent = os.path.dirname(os.path.abspath(output_path))
    if parent:
        os.makedirs(parent, exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)
        print(f"  Report saved → {output_path}")
        return True
    except IOError as exc:
        logging.getLogger(__name__).error(
            "Could not write report file %s: %s", output_path, exc
        )
        return False
