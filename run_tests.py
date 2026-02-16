#!/usr/bin/env python3
"""
Comprehensive Test Runner for Python Sprite Viewer
Runs tests with coverage analysis and generates reports.
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


class TestRunner:
    """Manages test execution with various options and reporting."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.python_cmd = self._get_python_cmd()

    def _get_python_cmd(self):
        """Get the appropriate Python command."""
        venv_dirs = [self.project_root / ".venv", self.project_root / "venv"]
        for venv_path in venv_dirs:
            if sys.platform == "win32":
                python_exe = venv_path / "Scripts" / "python.exe"
            else:
                python_exe = venv_path / "bin" / "python"

            if python_exe.exists():
                return str(python_exe)

        return sys.executable

    def has_module(self, module_name):
        """Check whether a module can be imported in the active environment."""
        result = subprocess.run(
            [self.python_cmd, "-c", f"import {module_name}"], capture_output=True, text=True
        )
        return result.returncode == 0

    def run_command(self, cmd, capture_output=False):
        """Run a command and optionally capture output."""
        print(f"Running: {' '.join(cmd)}")

        if capture_output:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode, result.stdout, result.stderr
        else:
            return subprocess.run(cmd).returncode, "", ""

    def install_dependencies(self):
        """Install dependencies using uv."""
        print("\nChecking dependencies with uv...")
        uv_cmd = shutil.which("uv")
        if not uv_cmd:
            print("uv is not installed. Install uv and run: uv sync --all-extras")
            sys.exit(1)

        cmd = [uv_cmd, "sync", "--all-extras"]
        returncode, _, _ = self.run_command(cmd)
        if returncode == 0:
            print("Dependencies installed successfully")
        else:
            print("Failed to install dependencies")
            sys.exit(1)

    def run_tests(self, args):
        """Run tests with specified options."""
        print("\nRunning tests...")

        # Base pytest command
        cmd = [self.python_cmd, "-m", "pytest"]

        # Add common options
        cmd.extend(["-v", "--tb=short"])

        # Coverage options
        if args.coverage:
            cmd.extend(
                [
                    "--cov=.",
                    "--cov-report=html:htmlcov",
                    "--cov-report=term-missing",
                    "--cov-report=json",
                    "--cov-report=xml",
                    f"--cov-config={self.project_root}/pyproject.toml",
                ]
            )

        # Test selection
        if args.unit:
            cmd.extend(["-m", "unit"])
        elif args.integration:
            cmd.extend(["-m", "integration"])
        elif args.ui:
            cmd.extend(["-m", "ui"])
        elif args.performance:
            cmd.extend(["-m", "performance"])
        elif args.smoke:
            cmd.extend(["-m", "smoke"])

        # Specific test files/patterns
        if args.tests:
            cmd.extend(args.tests)
        else:
            cmd.append("tests/")

        # Additional pytest options
        if args.verbose:
            cmd.append("-vv")

        if args.quiet:
            cmd.append("-q")

        if args.exitfirst:
            cmd.append("-x")

        if args.lf:
            cmd.append("--lf")

        if args.parallel:
            if not self.has_module("xdist"):
                print("pytest-xdist is not installed. Run `uv sync --all-extras`.")
                return 1
            cmd.extend(["-n", str(args.parallel)])

        # Exclude archived tests
        cmd.extend(["--ignore=archive/", "--ignore=build/", "--ignore=dist/"])

        # Run the tests
        start_time = time.time()
        returncode, _stdout, _stderr = self.run_command(cmd)
        duration = time.time() - start_time

        print(f"\n⏱️  Test execution time: {duration:.2f} seconds")

        # Generate reports
        if args.coverage and returncode == 0:
            self.generate_coverage_report()

        return returncode

    def generate_coverage_report(self):
        """Generate and display coverage report."""
        print("\nCoverage Report Summary:")

        # Read JSON coverage report
        coverage_file = Path("coverage.json")
        if coverage_file.exists():
            with open(coverage_file) as f:
                coverage_data = json.load(f)

            total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
            print(f"\nTotal Coverage: {total_coverage:.1f}%")

            # Show file coverage
            print("\nFile Coverage:")
            files = coverage_data.get("files", {})

            # Sort by coverage percentage
            sorted_files = sorted(
                files.items(), key=lambda x: x[1]["summary"]["percent_covered"], reverse=True
            )

            for filepath, data in sorted_files[:20]:  # Show top 20
                # Skip test files and __pycache__
                if "test" in filepath or "__pycache__" in filepath:
                    continue

                percent = data["summary"]["percent_covered"]
                # Show relative path
                rel_path = Path(filepath).relative_to(self.project_root)
                print(f"  {percent:5.1f}% - {rel_path}")

            print("\nHTML report generated at: htmlcov/index.html")

    def run_specific_test_suites(self):
        """Run specific test suites with descriptions."""
        test_suites = {
            "wizard": {
                "desc": "Export Wizard Tests",
                "pattern": "tests/ui/test_export_dialog.py tests/unit/test_export_wizard_workflow.py",
            },
            "export": {
                "desc": "All Export System Tests",
                "pattern": "tests/**/test_export*.py tests/**/test_frame_exporter.py",
            },
            "ui": {"desc": "UI Component Tests", "pattern": "tests/ui/"},
            "core": {
                "desc": "Core Functionality Tests",
                "pattern": "tests/unit/test_sprite_model.py tests/unit/test_*controller.py",
            },
            "integration": {"desc": "Integration Tests", "pattern": "tests/integration/"},
        }

        print("\nAvailable Test Suites:")
        for name, info in test_suites.items():
            print(f"  {name}: {info['desc']}")

        return test_suites

    def run_watch_mode(self):
        """Run tests in watch mode (requires pytest-watcher)."""
        print("\nRunning tests in watch mode...")
        if not shutil.which("ptw"):
            print("pytest-watcher is not installed. Run `uv sync --all-extras`.")
            return 1

        cmd = ["ptw", "--", "-v", "--tb=short"]
        return subprocess.run(cmd).returncode

    def generate_test_report(self):
        """Generate a comprehensive test report."""
        print("\nGenerating Test Report...")
        if not self.has_module("pytest_jsonreport"):
            print("pytest-json-report is not installed. Run `uv sync --all-extras`.")
            return 1

        # Run tests with JSON report
        cmd = [
            self.python_cmd,
            "-m",
            "pytest",
            "--json-report",
            "--json-report-file=test_report.json",
            "-v",
            "tests/",
        ]

        returncode, _, _ = self.run_command(cmd, capture_output=True)

        if returncode == 0 and Path("test_report.json").exists():
            with open("test_report.json") as f:
                report = json.load(f)

            print("\nTest Summary:")
            summary = report.get("summary", {})
            print(f"  Total tests: {summary.get('total', 0)}")
            print(f"  Passed: {summary.get('passed', 0)}")
            print(f"  Failed: {summary.get('failed', 0)}")
            print(f"  Skipped: {summary.get('skipped', 0)}")
            print(f"  Duration: {report.get('duration', 0):.2f}s")

        return returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for Python Sprite Viewer"
    )

    # Test selection
    parser.add_argument("tests", nargs="*", help="Specific test files or patterns")
    parser.add_argument("-u", "--unit", action="store_true", help="Run only unit tests")
    parser.add_argument(
        "-i", "--integration", action="store_true", help="Run only integration tests"
    )
    parser.add_argument("--ui", action="store_true", help="Run only UI tests")
    parser.add_argument("-p", "--performance", action="store_true", help="Run performance tests")
    parser.add_argument("-s", "--smoke", action="store_true", help="Run smoke tests only")

    # Coverage options
    parser.add_argument("-c", "--coverage", action="store_true", help="Generate coverage report")

    # Output options
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Minimal output")

    # Execution options
    parser.add_argument("-x", "--exitfirst", action="store_true", help="Exit on first failure")
    parser.add_argument("--lf", action="store_true", help="Run last failed tests")
    parser.add_argument("-n", "--parallel", type=int, help="Run tests in parallel")

    # Special modes
    parser.add_argument("-w", "--watch", action="store_true", help="Run tests in watch mode")
    parser.add_argument("--install", action="store_true", help="Install test dependencies")
    parser.add_argument("--report", action="store_true", help="Generate detailed test report")
    parser.add_argument("--suites", action="store_true", help="Show available test suites")

    args = parser.parse_args()

    runner = TestRunner()

    # Handle special modes
    if args.install:
        runner.install_dependencies()
        return

    if args.suites:
        runner.run_specific_test_suites()
        return

    if args.watch:
        sys.exit(runner.run_watch_mode())

    if args.report:
        sys.exit(runner.generate_test_report())

    # Run tests
    returncode = runner.run_tests(args)
    sys.exit(returncode)


if __name__ == "__main__":
    main()
