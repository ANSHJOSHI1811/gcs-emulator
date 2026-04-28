#!/bin/bash
# CloudTester - Full Test Suite Runner with HTML Reports
# Runs the complete test suite across all services to check for regressions
# Usage: ./tests/run_full_suite.sh [--parallel] [--coverage] [--gcloud] [--marker MARKER]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TESTS_DIR="$SCRIPT_DIR/CloudTester/suites"
ENV_FILE="$SCRIPT_DIR/.env-test"
REPORTS_DIR="$PROJECT_ROOT/htmlcov"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Load environment
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

# Parse arguments
PARALLEL_ENABLED=false
COVERAGE_ENABLED=false
GCLOUD_ENABLED=true
MARKER=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --parallel)
            PARALLEL_ENABLED=true
            shift
            ;;
        --coverage)
            COVERAGE_ENABLED=true
            shift
            ;;
        --gcloud)
            GCLOUD_ENABLED=true
            shift
            ;;
        --no-gcloud)
            GCLOUD_ENABLED=false
            shift
            ;;
        --marker)
            MARKER="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         CloudTester - Full Regression Test Suite${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Configuration:${NC}"
echo "  Test Directory: $TESTS_DIR"
echo "  API URL: $TEST_API_URL"
echo "  Project: $TEST_PROJECT"
echo "  Zone: $TEST_ZONE"
echo "  Parallel: $([ "$PARALLEL_ENABLED" = true ] && echo "Yes" || echo "No")"
echo "  Coverage: $([ "$COVERAGE_ENABLED" = true ] && echo "Yes" || echo "No")"
echo "  GCloud: $([ "$GCLOUD_ENABLED" = true ] && echo "Enabled ☁️ " || echo "Disabled")"
if [ -n "$MARKER" ]; then
    echo "  Marker: $MARKER"
fi
echo ""

# Create reports directory
mkdir -p "$REPORTS_DIR"

# Build pytest command
PYTEST_ARGS="-v --tb=short --strict-markers"

# Always generate HTML report
PYTEST_ARGS="$PYTEST_ARGS --html=$REPORTS_DIR/full-suite-report.html --self-contained-html"
echo -e "${YELLOW}📊 Generating HTML test report...${NC}"

if [ "$PARALLEL_ENABLED" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -n auto"
    echo -e "${YELLOW}⚡ Running tests in parallel...${NC}"
fi

if [ "$COVERAGE_ENABLED" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=minimal-backend --cov-report=html --cov-report=term-missing"
    echo -e "${YELLOW}� Collecting code coverage...${NC}"
fi

# Enable gcloud integration by default
if [ "$GCLOUD_ENABLED" = true ]; then
    export ENABLE_GCLOUD_TESTS=true
    echo -e "${YELLOW}☁️  GCloud integration enabled${NC}"
else
    export ENABLE_GCLOUD_TESTS=false
    echo -e "${YELLOW}☁️  GCloud integration disabled${NC}"
fi

if [ -n "$MARKER" ]; then
    PYTEST_ARGS="$PYTEST_ARGS -m $MARKER"
fi

# Check if test directory exists
if [ ! -d "$TESTS_DIR" ]; then
    echo -e "${RED}✗ Test directory not found: $TESTS_DIR${NC}"
    exit 1
fi

# Count test files
TEST_COUNT=$(find "$TESTS_DIR" -name "test_*.py" -type f | wc -l)
if [ $TEST_COUNT -eq 0 ]; then
    echo -e "${YELLOW}⚠ No test files found in $TESTS_DIR${NC}"
    exit 0
fi

echo -e "${CYAN}Found $TEST_COUNT test suites${NC}"
echo ""

cd "$PROJECT_ROOT"

# Run pytest
echo -e "${YELLOW}Starting test execution...${NC}"
echo -e "${BLUE}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""

START_TIME=$(date +%s)

pytest "$TESTS_DIR" $PYTEST_ARGS -s 2>&1 | tee /tmp/full_suite_output.txt

TEST_RESULT=${PIPESTATUS[0]}
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║ Test Results (Duration: ${DURATION}s)${NC}"
echo -e "${BLUE}╠════════════════════════════════════════════════════════════════╣${NC}"

if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}║✓ All tests PASSED${NC}"
else
    echo -e "${RED}║✗ Some tests FAILED${NC}"
    echo -e "${RED}║${NC}"
    echo -e "${RED}║ Failed tests summary:${NC}"
    grep -E "FAILED|ERROR" /tmp/full_suite_output.txt | head -20 || true
fi

echo -e "${BLUE}║${NC}"
echo -e "${BLUE}║ 📊 Reports:${NC}"
echo -e "${BLUE}║   Test Report:     htmlcov/full-suite-report.html${NC}"

if [ "$COVERAGE_ENABLED" = true ]; then
    echo -e "${BLUE}║   Coverage Report: htmlcov/index.html${NC}"
fi

echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${CYAN}"
echo "✅ Test report generated at: $REPORTS_DIR/full-suite-report.html"
if [ "$COVERAGE_ENABLED" = true ]; then
    echo "✅ Coverage report generated at: $REPORTS_DIR/index.html"
fi
echo -e "${NC}"
echo ""

exit $TEST_RESULT
