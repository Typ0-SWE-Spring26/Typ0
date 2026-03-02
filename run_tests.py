"""Cross-platform test runner. Works on Windows, macOS, and Linux.

Usage:
    python run_tests.py          # run all tests
    python run_tests.py -v       # verbose output
    python run_tests.py -x       # stop on first failure
"""
import subprocess
import sys


def main():
    args = [sys.executable, "-m", "pytest", "tests/", *sys.argv[1:]]
    raise SystemExit(subprocess.call(args))


if __name__ == "__main__":
    main()
