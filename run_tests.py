#!/usr/bin/env python3
"""
Test runner for Python Sprite Viewer
=====================================

Professional test runner with multiple execution modes and reporting options.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run only unit tests
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --coverage         # Run with coverage report
    python run_tests.py --performance      # Run performance tests
    python run_tests.py --smoke            # Run smoke tests only
    python run_tests.py --watch            # Watch mode for development
"""

import sys
import argparse
import subprocess
from pathlib import Path


class TestRunner:
    """Professional test runner with multiple execution modes."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.tests_dir = self.project_root / "tests"
    
    def run_unit_tests(self, extra_args=None):
        """Run unit tests only."""
        cmd = [
            "python", "-m", "pytest",
            "-m", "unit",
            "--tb=short",
            "-v"
        ]
        if extra_args:
            cmd.extend(extra_args)
        
        print("🧪 Running Unit Tests...")
        return subprocess.run(cmd, cwd=self.project_root)
    
    def run_integration_tests(self, extra_args=None):
        """Run integration tests only."""
        cmd = [
            "python", "-m", "pytest", 
            "-m", "integration",
            "--tb=short",
            "-v"
        ]
        if extra_args:
            cmd.extend(extra_args)
        
        print("🔗 Running Integration Tests...")
        return subprocess.run(cmd, cwd=self.project_root)
    
    def run_ui_tests(self, extra_args=None):
        """Run UI tests (requires display)."""
        cmd = [
            "python", "-m", "pytest",
            "-m", "ui",
            "--tb=short", 
            "-v"
        ]
        if extra_args:
            cmd.extend(extra_args)
        
        print("🖥️  Running UI Tests...")
        return subprocess.run(cmd, cwd=self.project_root)
    
    def run_performance_tests(self, extra_args=None):
        """Run performance tests."""
        cmd = [
            "python", "-m", "pytest",
            "-m", "performance",
            "--tb=short",
            "-v",
            "--benchmark-only"
        ]
        if extra_args:
            cmd.extend(extra_args)
        
        print("⚡ Running Performance Tests...")
        return subprocess.run(cmd, cwd=self.project_root)
    
    def run_smoke_tests(self, extra_args=None):
        """Run smoke tests for critical functionality."""
        cmd = [
            "python", "-m", "pytest",
            "-m", "smoke",
            "--tb=short",
            "-v",
            "--maxfail=1"
        ]
        if extra_args:
            cmd.extend(extra_args)
        
        print("💨 Running Smoke Tests...")
        return subprocess.run(cmd, cwd=self.project_root)
    
    def run_all_tests(self, extra_args=None):
        """Run all tests."""
        cmd = [
            "python", "-m", "pytest",
            "--tb=short",
            "-v"
        ]
        if extra_args:
            cmd.extend(extra_args)
        
        print("🚀 Running All Tests...")
        return subprocess.run(cmd, cwd=self.project_root)
    
    def run_with_coverage(self, test_type="all", extra_args=None):
        """Run tests with coverage reporting."""
        cmd = [
            "python", "-m", "pytest",
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml",
            "--tb=short",
            "-v"
        ]
        
        # Add marker filter based on test type
        if test_type != "all":
            cmd.extend(["-m", test_type])
        
        if extra_args:
            cmd.extend(extra_args)
        
        print(f"📊 Running {test_type.title()} Tests with Coverage...")
        result = subprocess.run(cmd, cwd=self.project_root)
        
        if result.returncode == 0:
            print("\n📈 Coverage report generated in htmlcov/index.html")
        
        return result
    
    def run_parallel_tests(self, workers=4, extra_args=None):
        """Run tests in parallel using pytest-xdist."""
        cmd = [
            "python", "-m", "pytest",
            f"-n{workers}",
            "--tb=short",
            "-v"
        ]
        if extra_args:
            cmd.extend(extra_args)
        
        print(f"⚡ Running Tests in Parallel ({workers} workers)...")
        return subprocess.run(cmd, cwd=self.project_root)
    
    def watch_tests(self):
        """Run tests in watch mode for development."""
        try:
            cmd = [
                "python", "-m", "pytest-watch",
                "--",
                "-m", "unit",
                "--tb=short"
            ]
            print("👀 Starting test watch mode (Ctrl+C to stop)...")
            return subprocess.run(cmd, cwd=self.project_root)
        except KeyboardInterrupt:
            print("\n🛑 Test watch mode stopped.")
            return subprocess.CompletedProcess([], 0)
    
    def run_quality_checks(self):
        """Run code quality checks alongside tests."""
        print("🔍 Running Code Quality Checks...")
        
        # Run tests with additional quality plugins
        cmd = [
            "python", "-m", "pytest",
            "--flake8",
            "--mypy", 
            "--black",
            "--tb=short",
            "-v"
        ]
        
        return subprocess.run(cmd, cwd=self.project_root)
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        cmd = [
            "python", "-m", "pytest",
            "--html=test_report.html",
            "--json-report",
            "--json-report-file=test_report.json",
            "--cov=.",
            "--cov-report=html",
            "--tb=short",
            "-v"
        ]
        
        print("📋 Generating Comprehensive Test Report...")
        result = subprocess.run(cmd, cwd=self.project_root)
        
        if result.returncode == 0:
            print("\n📄 Test report generated:")
            print("  - HTML: test_report.html")
            print("  - JSON: test_report.json") 
            print("  - Coverage: htmlcov/index.html")
        
        return result


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Python Sprite Viewer Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                     # Run all tests
  python run_tests.py --unit --coverage   # Unit tests with coverage
  python run_tests.py --smoke             # Quick smoke tests
  python run_tests.py --parallel 8        # Parallel execution
  python run_tests.py --watch             # Development watch mode
        """
    )
    
    # Test type selection
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--ui", action="store_true", help="Run UI tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--smoke", action="store_true", help="Run smoke tests only")
    
    # Execution options
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--parallel", type=int, metavar="N", help="Run tests in parallel with N workers")
    parser.add_argument("--watch", action="store_true", help="Watch mode for development")
    parser.add_argument("--quality", action="store_true", help="Run code quality checks")
    parser.add_argument("--report", action="store_true", help="Generate comprehensive test report")
    
    # Additional pytest arguments
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--maxfail", type=int, metavar="N", help="Stop after N failures")
    parser.add_argument("--timeout", type=int, metavar="SECONDS", help="Timeout for individual tests")
    parser.add_argument("pytest_args", nargs="*", help="Additional arguments to pass to pytest")
    
    args = parser.parse_args()
    
    # Create test runner
    runner = TestRunner()
    
    # Build extra arguments
    extra_args = args.pytest_args or []
    if args.verbose:
        extra_args.append("-v")
    if args.maxfail:
        extra_args.extend(["--maxfail", str(args.maxfail)])
    if args.timeout:
        extra_args.extend(["--timeout", str(args.timeout)])
    
    # Determine execution mode
    if args.watch:
        result = runner.watch_tests()
    elif args.quality:
        result = runner.run_quality_checks()
    elif args.report:
        result = runner.generate_test_report()
    elif args.parallel:
        result = runner.run_parallel_tests(args.parallel, extra_args)
    elif args.coverage:
        test_type = "all"
        if args.unit:
            test_type = "unit"
        elif args.integration:
            test_type = "integration"
        elif args.ui:
            test_type = "ui"
        elif args.performance:
            test_type = "performance"
        result = runner.run_with_coverage(test_type, extra_args)
    elif args.unit:
        result = runner.run_unit_tests(extra_args)
    elif args.integration:
        result = runner.run_integration_tests(extra_args)
    elif args.ui:
        result = runner.run_ui_tests(extra_args)
    elif args.performance:
        result = runner.run_performance_tests(extra_args)
    elif args.smoke:
        result = runner.run_smoke_tests(extra_args)
    else:
        result = runner.run_all_tests(extra_args)
    
    # Exit with test result code
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()