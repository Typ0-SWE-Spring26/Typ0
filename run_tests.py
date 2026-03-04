"""Cross-platform test runner. Works on Windows, macOS, and Linux.

Usage:
    python run_tests.py              # run unit tests (browser tests excluded)
    python run_tests.py -v           # verbose output
    python run_tests.py -x           # stop on first failure
    python run_tests.py -m browser   # run browser tests only (requires venv + pygbag server)
"""
import subprocess
import sys


def main():
    # Exclude browser tests by default — they need pytest-playwright (venv) and
    # a running pygbag server on port 8080.  Pass -m browser to run them explicitly.
    extra = sys.argv[1:]
    if not any(a.startswith("-m") or a == "browser" for a in extra):
        extra = ["-m", "not browser"] + extra
    args = [sys.executable, "-m", "pytest", "tests/", *extra]
    raise SystemExit(subprocess.call(args))


if __name__ == "__main__":
    main()
