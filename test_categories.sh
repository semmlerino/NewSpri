#!/bin/bash
# Test category runner for Python Sprite Viewer
# Provides convenient shortcuts for running different test suites

# Activate virtual environment
source venv/bin/activate

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[TEST]${NC} $1"
}

# Function to print error
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

case "$1" in
    unit)
        print_status "Running unit tests..."
        pytest -m unit --tb=short --durations=10
        ;;
    integration)
        print_status "Running integration tests..."
        pytest -m integration --tb=short --durations=10
        ;;
    ui)
        print_status "Running UI tests..."
        pytest -m ui --tb=short --durations=10
        ;;
    fast)
        print_status "Running fast tests (excluding slow)..."
        pytest -m "not slow" --tb=short --maxfail=5
        ;;
    coverage)
        print_status "Running tests with coverage..."
        pytest --cov=. --cov-report=html --cov-report=term-missing --cov-report=json
        print_status "Coverage report generated at htmlcov/index.html"
        ;;
    watch)
        print_status "Starting test watcher..."
        ptw -- -x --lf --tb=short
        ;;
    parallel)
        print_status "Running tests in parallel..."
        pytest -n auto --tb=short
        ;;
    performance)
        print_status "Running performance tests..."
        pytest -m performance --tb=short --benchmark-only
        ;;
    smoke)
        print_status "Running smoke tests..."
        pytest -m smoke --tb=short --maxfail=1
        ;;
    report)
        print_status "Running tests with HTML report..."
        pytest --html=test-report.html --self-contained-html --tb=short
        print_status "Report generated at test-report.html"
        ;;
    debug)
        print_status "Running tests in debug mode..."
        pytest -vvv --pdb --capture=no -x
        ;;
    quick)
        print_status "Running quick unit tests..."
        pytest tests/unit/test_config.py tests/unit/test_animation_controller.py -v
        ;;
    all)
        print_status "Running all tests..."
        pytest --tb=short --durations=20
        ;;
    *)
        echo "Python Sprite Viewer Test Runner"
        echo "================================"
        echo ""
        echo "Usage: $0 {command}"
        echo ""
        echo "Commands:"
        echo "  unit        - Run unit tests only"
        echo "  integration - Run integration tests only"
        echo "  ui          - Run UI tests only"
        echo "  fast        - Run all tests except slow ones"
        echo "  coverage    - Run tests with coverage report"
        echo "  watch       - Run tests in watch mode"
        echo "  parallel    - Run tests in parallel (all CPUs)"
        echo "  performance - Run performance benchmarks"
        echo "  smoke       - Run critical smoke tests"
        echo "  report      - Generate HTML test report"
        echo "  debug       - Run tests in debug mode (pdb on failure)"
        echo "  quick       - Run a few quick unit tests"
        echo "  all         - Run all tests"
        echo ""
        echo "Examples:"
        echo "  $0 unit       # Run unit tests"
        echo "  $0 coverage   # Generate coverage report"
        echo "  $0 watch      # Start test watcher"
        exit 1
        ;;
esac

# Check exit code and print summary
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    print_status "Tests completed successfully!"
else
    print_error "Tests failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE