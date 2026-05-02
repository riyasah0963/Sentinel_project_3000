"""
utils.py – CLI output helpers and ANSI colour support for Sentinel.

ANSI colour codes are used to produce colour-coded terminal output:
    GREEN  – added files / success messages
    RED    – deleted files / error messages
    YELLOW – modified or skipped files / warnings
    CYAN   – headers and separators
    RESET  – restore default terminal colour

Colour output is automatically disabled when stdout is not a TTY (e.g.
when piping to a file) to avoid polluting plain-text output with escape
sequences.
"""

import os
import sys

# Detect whether the terminal supports ANSI escape codes.
# Disable colour when stdout is redirected to a file or pipe.
_COLOUR_SUPPORTED = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

# ANSI escape codes
GREEN  = "\033[92m" if _COLOUR_SUPPORTED else ""
RED    = "\033[91m" if _COLOUR_SUPPORTED else ""
YELLOW = "\033[93m" if _COLOUR_SUPPORTED else ""
CYAN   = "\033[96m" if _COLOUR_SUPPORTED else ""
BOLD   = "\033[1m"  if _COLOUR_SUPPORTED else ""
RESET  = "\033[0m"  if _COLOUR_SUPPORTED else ""


def colour(text: str, code: str) -> str:
    """
    Wrap *text* in the given ANSI *code* and reset afterwards.

    Args:
        text (str): The string to colour.
        code (str): An ANSI escape code constant (GREEN, RED, etc.).

    Returns:
        str: Coloured string (or plain string if colour is unsupported).
    """
    return f"{code}{text}{RESET}"


def print_banner(version: str) -> None:
    """
    Print the Sentinel ASCII banner with version information.

    Args:
        version (str): Version string to display (e.g. "1.0.0").
    """
    banner = f"""
{CYAN}{BOLD}
  ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗
  ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║
  ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║
  ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║
  ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
  ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
{RESET}
  {BOLD}File Integrity Monitoring System  v{version}{RESET}
  COMP3000 Computing Project – University of Plymouth
"""
    print(banner)


def print_success(message: str) -> None:
    """Print a green success message."""
    print(f"{GREEN}[✔] {message}{RESET}")


def print_error(message: str) -> None:
    """Print a red error message to stderr."""
    print(f"{RED}[✖] ERROR: {message}{RESET}", file=sys.stderr)


def print_info(message: str) -> None:
    """Print a cyan informational message."""
    print(f"{CYAN}[i] {message}{RESET}")


def print_warning(message: str) -> None:
    """Print a yellow warning message."""
    print(f"{YELLOW}[⚠] {message}{RESET}")
