# Sentinel File Integrity Monitoring System

**COMP3000 Computing Project**  
*Student:* Riya Shah  
*University:* University of Plymouth

---

## Overview

Sentinel is a Python-based File Integrity Monitoring (FIM) system that detects unauthorised file modifications using SHA-256 cryptographic hashing. It creates a trusted baseline snapshot of a directory and compares future scans against it to identify:

- Files that have been **modified** (hash changed)
- Files that have been **added** (new since baseline)
- Files that have been **deleted** (removed since baseline)

Sentinel demonstrates security principles used in cybersecurity intrusion detection and host integrity monitoring, and is built entirely on the Python standard library — no external runtime dependencies.

---

## Features

- SHA-256 cryptographic file hashing (64 KB chunked reads for large-file support)
- Baseline snapshot generation with metadata (version, timestamp, file sizes)
- Recursive directory scanning with deterministic ordering
- ANSI colour-coded terminal output (auto-disabled when piping)
- JSON report generation for archival or SIEM integration
- Command-line interface built with `argparse`
- Comprehensive pytest test suite (49 tests, 48 pass, 1 skipped on Windows)
- 87% code coverage across all modules

---

## Technologies

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Hashing | `hashlib` (SHA-256) |
| CLI | `argparse` |
| Serialisation | `json` |
| Testing | `pytest`, `pytest-cov` |
| Linting | `flake8`, `black` |
| Version control | Git / GitHub |

---

## Project Structure

```
sentinel/
│
├── sentinel.py              # CLI entry point (argparse)
│
├── core/
│   ├── __init__.py
│   ├── baseline.py          # Baseline creation & JSON persistence
│   ├── checker.py           # Integrity comparison engine
│   ├── hasher.py            # SHA-256 hashing (chunked reads)
│   ├── scanner.py           # Recursive directory scanner
│   ├── logger.py            # Logging config & report serialisation
│   └── utils.py             # ANSI colour helpers & CLI output
│
├── tests/
│   ├── test_baseline.py     # Unit tests for baseline module
│   ├── test_checker.py      # Integration tests for integrity check
│   ├── test_hasher.py       # Unit tests for SHA-256 hashing
│   ├── test_scanner.py      # Unit tests for directory scanner
│   └── test_logger.py       # Unit tests for logger module
│
├── test_project/            # Sample directory used for demonstration
│   ├── main.py
│   └── config.py
│
├── baseline.json            # Example baseline snapshot
└── my_report.json           # Example comparison report
```

---

## Installation

No external packages are required to run Sentinel. For testing and coverage reporting:

```bash
pip install pytest pytest-cov
```

---

## Usage

### 1. Create a Baseline

Generate a trusted snapshot of a directory:

```bash
python sentinel.py --init baseline.json --path ./test_project
```

Output includes:
- Number of files hashed
- Number of files skipped (permission errors)
- Time taken
- Saved baseline path

### 2. Check Integrity

Compare the current directory state against the stored baseline:

```bash
python sentinel.py --check baseline.json --path ./test_project
```

Sentinel reports every change — added, deleted, or modified — with colour-coded output.

### 3. Optional Flags

```bash
# Print every file processed (including unchanged)
python sentinel.py --check baseline.json --path ./test_project --verbose

# Save a JSON report for archival or SIEM integration
python sentinel.py --check baseline.json --path ./test_project --report report.json

# Show version
python sentinel.py --version
```

---

## Example Output

### Baseline Creation

```
[i] Creating baseline for: /home/user/test_project
[✔] Baseline created → baseline.json
      Files hashed : 3
      Files skipped: 0
      Time taken   : 0.001s
```

### Integrity Check (with changes)

```
────────────────────────────────────────────────────────────
  Sentinel Integrity Report
────────────────────────────────────────────────────────────

  ADDED (1 file(s))
    ✔  [ADDED]    malware.txt

  DELETED (1 file(s))
    ✖  [DELETED]  README.md

  MODIFIED (1 file(s))
    ⚠  [MODIFIED] config.py
       Baseline SHA-256 : 488a9d...
       Current  SHA-256 : 7f3c21...

────────────────────────────────────────────────────────────
  Summary: 1 added  1 deleted  1 modified  1 unchanged
  Scan completed in 0.002s
────────────────────────────────────────────────────────────
```

---

## JSON Baseline Format

```json
{
  "sentinel_version": "1.0.0",
  "schema_version": 1,
  "created_at": "2026-04-22T19:48:57.831992+00:00",
  "base_path": "/home/user/test_project",
  "total_files": 3,
  "skipped_files": [],
  "elapsed_seconds": 0.001,
  "files": {
    "config.py": {
      "sha256": "488a9d...",
      "size_bytes": 16
    },
    "main.py": {
      "sha256": "db41c2...",
      "size_bytes": 17
    }
  }
}
```

---

## Testing

Run the full test suite:

```bash
pytest tests/ -v
```

Run with coverage report:

```bash
pytest tests/ --cov=core --cov-report=term-missing
```

Expected results:

```
49 tests collected
48 passed, 1 skipped (chmod not reliable on Windows)

Name               Stmts   Miss  Cover
--------------------------------------
core/baseline.py      71     14    80%
core/checker.py       87      7    92%
core/hasher.py        20      2    90%
core/logger.py        23      0   100%
core/scanner.py       36      7    81%
core/utils.py         22      4    82%
--------------------------------------
TOTAL                259     34    87%
```

---

## Security Design

### SHA-256 Hashing

Each file is hashed with SHA-256 (via Python's `hashlib`), producing a unique 64-character hex digest. Files are read in 64 KB chunks, ensuring memory efficiency for arbitrarily large files.

### Baseline Trust Model

The baseline JSON stores the known-good state of the monitored directory. Any deviation detected during `--check` is flagged for review.

### Change Detection

Three categories of change are detected and reported:

| Category | Meaning |
|----------|---------|
| ADDED | File exists now but was not in the baseline |
| DELETED | File was in the baseline but no longer on disk |
| MODIFIED | File exists in both but the SHA-256 hash differs |

---

## Future Improvements

- Real-time monitoring via `watchdog`
- HMAC-signed baselines (tamper-proof storage)
- Email or webhook alerting on change detection
- HTML report generation
- Parallel hashing for very large directories

---

## Author

**Riya Shah**  
COMP3000 Computing Project  
University of Plymouth  
2025–2026
