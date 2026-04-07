#!/usr/bin/env python
"""
Script to run integration tests with proper configuration.
Ensures Docker is running and dependencies are installed.
"""

import subprocess
import sys
from pathlib import Path


def check_docker():
    """Check if Docker is running."""
    print("🐳 Checking Docker status...")
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print("❌ Docker is not running. Please start Docker Desktop and try again.")
            return False
        print("✅ Docker is running")
        return True
    except FileNotFoundError:
        print("❌ Docker is not installed. Please install Docker Desktop.")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n📦 Checking dependencies...")
    try:
        import pytest  # noqa: F401
        import sqlalchemy  # noqa: F401
        import testcontainers  # noqa: F401

        print("✅ All dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e.name}")
        print("Run: pip install -r requirements.txt")
        return False


def run_tests(args: list[str] | None = None):
    """Run integration tests."""
    print("\n🧪 Running integration tests...\n")

    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    tests_dir = script_dir / "tests"

    # Find all integration test files
    test_files = list(tests_dir.glob("integration_test_*.py"))

    if not test_files:
        print("❌ No integration test files found!")
        return 1

    print(f"Found {len(test_files)} test file(s):")
    for test_file in test_files:
        print(f"  - {test_file.name}")
    print()

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        "--tb=short",
    ]

    # Add all test files
    cmd.extend([str(f) for f in test_files])

    if args:
        cmd.extend(args)

    result = subprocess.run(cmd, cwd=str(script_dir))
    return result.returncode


def main():
    """Main entry point."""
    print("=" * 60)
    print("Integration Test Runner")
    print("=" * 60)

    # Check prerequisites
    if not check_docker():
        sys.exit(1)

    if not check_dependencies():
        sys.exit(1)

    # Get additional arguments from command line
    additional_args = sys.argv[1:] if len(sys.argv) > 1 else None

    # Run tests
    exit_code = run_tests(additional_args)

    print("\n" + "=" * 60)
    if exit_code == 0:
        print("✅ All integration tests passed!")
    else:
        print("❌ Some tests failed. Check output above.")
    print("=" * 60)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
