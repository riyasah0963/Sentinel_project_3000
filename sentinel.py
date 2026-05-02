"""
sentinel.py – Entry point for the Sentinel File Integrity Monitoring System.

Usage:
    python sentinel.py --init <baseline.json> --path <directory>
    python sentinel.py --check <baseline.json> --path <directory>
    python sentinel.py --init <baseline.json> --path <directory> --verbose
    python sentinel.py --check <baseline.json> --path <directory> --report report.json

Author: Riya Shah
Module: COMP3000 Computing Project
Version: 1.0.0
"""

import argparse
import sys

from core.baseline import create_baseline
from core.checker import check_integrity
from core.utils import print_banner, print_error

VERSION = "1.0.0"


def build_parser():
    """
    Build and return the argument parser for Sentinel.

    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="sentinel",
        description="Sentinel – File Integrity Monitoring System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python sentinel.py --init baseline.json --path ./myproject\n"
            "  python sentinel.py --check baseline.json --path ./myproject\n"
            "  python sentinel.py --check baseline.json --path ./myproject --verbose\n"
        ),
    )
    parser.add_argument(
        "--init",
        metavar="BASELINE_FILE",
        help="Create a new baseline snapshot and save to BASELINE_FILE (JSON).",
    )
    parser.add_argument(
        "--check",
        metavar="BASELINE_FILE",
        help="Compare current state against BASELINE_FILE and report changes.",
    )
    parser.add_argument(
        "--path",
        required=True,
        metavar="DIRECTORY",
        help="Path to the directory (or file) to monitor.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print every file processed during scanning.",
    )
    parser.add_argument(
        "--report",
        metavar="REPORT_FILE",
        help="Save the comparison report as a JSON file (used with --check).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Sentinel v{VERSION}",
    )
    return parser


def main():
    """
    Main entry point. Parses CLI arguments and dispatches to the
    appropriate module (baseline creation or integrity check).
    """
    print_banner(VERSION)
    parser = build_parser()
    args = parser.parse_args()

    # Validate: user must supply --init or --check
    if not args.init and not args.check:
        print_error("You must specify either --init or --check.")
        parser.print_help()
        sys.exit(1)

    if args.init and args.check:
        print_error("Use either --init or --check, not both.")
        sys.exit(1)

    if args.init:
        success = create_baseline(
            path=args.path,
            baseline_file=args.init,
            verbose=args.verbose,
        )
        sys.exit(0 if success else 1)

    if args.check:
        success = check_integrity(
            path=args.path,
            baseline_file=args.check,
            verbose=args.verbose,
            report_file=args.report,
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
