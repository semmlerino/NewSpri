#!/usr/bin/env python3
"""
Comprehensive Test Runner for Python Sprite Viewer
Runs tests with coverage analysis and generates reports.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


class TestRunner:
    """Manages test execution with various options and reporting."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        self.python_cmd = self._get_python_cmd()

    def _get_python_cmd(self):
        """Get the appropriate Python command."""
        if sys.platform == "win32":
            python_exe = self.venv_path / "Scripts" / "python.exe"
        else:
            python_exe = self.venv_path / "bin" / "python"

        if python_exe.exists():
            return str(python_exe)
        return sys.executable

    def run_command(self, cmd, capture_output=False):
        """Run a command and optionally capture output."""
        print(f"Running: {' '.join(cmd)}")

        if capture_output:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode, result.stdout, result.stderr
        else:
            return subprocess.run(cmd).returncode, "", ""

    def install_dependencies(self):
        """Ensure test dependencies are installed."""
        print("\n🔧 Checking test dependencies...")

        deps = ["pytest", "pytest-qt", "pytest-cov", "pytest-benchmark", "coverage"]
        cmd = [self.python_cmd, "-m", "pip", "install", *deps]

        returncode, _, _ = self.run_command(cmd)
        if returncode == 0:
            print("✅ Dependencies installed successfully")
        else:
            print("❌ Failed to install dependencies")
            sys.exit(1)

    def run_tests(self, args):
        """Run tests with specified options."""
        print("\n🧪 Running tests...")

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
            cmd.extend(["-n", str(args.parallel)])
            # Install pytest-xdist if needed
            subprocess.run(
                [self.python_cmd, "-m", "pip", "install", "pytest-xdist"], capture_output=True
            )

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
        print("\n📊 Coverage Report Summary:")

        # Read JSON coverage report
        coverage_file = Path("coverage.json")
        if coverage_file.exists():
            with open(coverage_file) as f:
                coverage_data = json.load(f)

            total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
            print(f"\n✨ Total Coverage: {total_coverage:.1f}%")

            # Show file coverage
            print("\n📁 File Coverage:")
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

            print("\n📈 HTML report generated at: htmlcov/index.html")

    def run_specific_test_suites(self):
        """Run specific test suites with descriptions."""
        test_suites = {
            "wizard": {
                "desc": "Export Wizard Tests",
                "pattern": "tests/ui/test_export_wizard.py tests/unit/test_wizard_components.py",
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

        print("\n🎯 Available Test Suites:")
        for name, info in test_suites.items():
            print(f"  {name}: {info['desc']}")

        return test_suites

    def run_watch_mode(self):
        """Run tests in watch mode (requires pytest-watch)."""
        print("\n👁️  Running tests in watch mode...")

        # Install pytest-watch
        subprocess.run(
            [self.python_cmd, "-m", "pip", "install", "pytest-watch"], capture_output=True
        )

        cmd = [self.python_cmd, "-m", "ptw", "--", "-v", "--tb=short"]
        subprocess.run(cmd)

    def generate_test_report(self):
        """Generate a comprehensive test report."""
        print("\n📝 Generating Test Report...")

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

        # Install pytest-json-report if needed
        subprocess.run(
            [self.python_cmd, "-m", "pip", "install", "pytest-json-report"], capture_output=True
        )

        returncode, _, _ = self.run_command(cmd, capture_output=True)

        if returncode == 0 and Path("test_report.json").exists():
            with open("test_report.json") as f:
                report = json.load(f)

            print("\n📊 Test Summary:")
            summary = report.get("summary", {})
            print(f"  Total tests: {summary.get('total', 0)}")
            print(f"  Passed: {summary.get('passed', 0)}")
            print(f"  Failed: {summary.get('failed', 0)}")
            print(f"  Skipped: {summary.get('skipped', 0)}")
            print(f"  Duration: {report.get('duration', 0):.2f}s")


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
        runner.run_watch_mode()
        return

    if args.report:
        runner.generate_test_report()
        return

    # Run tests
    returncode = runner.run_tests(args)
    sys.exit(returncode)


if __name__ == "__main__":
    main()
