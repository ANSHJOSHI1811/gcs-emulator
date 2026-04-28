#!/bin/bash
# CloudTester - Wrapper Test Runner with HTML Reports
# Runs tests for a specific feature during development
# Generates HTML reports and supports gcloud testing (enabled by default)
# Usage: ./tests/run_wrapper_tests.sh [feature_name] [--no-gcloud] [--gcloud-only] [--api-only]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TESTS_DIR="$SCRIPT_DIR/CloudTester/wrappers"
SUITES_DIR="$SCRIPT_DIR/CloudTester/suites"
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
FEATURE=${1:-""}
GCLOUD_ENABLED=true  # Default: enabled
API_ENABLED=true      # Default: enabled

# Check for flags
shift || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-gcloud)
            GCLOUD_ENABLED=false
            shift
            ;;
        --gcloud-only)
            API_ENABLED=false
            shift
            ;;
        --api-only)
            GCLOUD_ENABLED=false
            shift
            ;;
        *)
            shift
            ;;
    esac
done

if [ -z "$FEATURE" ]; then
    echo -e "${YELLOW}Usage: ./run_wrapper_tests.sh [feature_name] [--no-gcloud] [--gcloud-only] [--api-only]${NC}"
    echo ""
    echo "Examples:"
    echo "  ./run_wrapper_tests.sh firewall          (runs both API + gcloud tests)"
    echo "  ./run_wrapper_tests.sh compute --no-gcloud  (API tests only)"
    echo "  ./run_wrapper_tests.sh gke --gcloud-only    (gcloud tests only)"
    echo ""
    echo "Available wrapper tests:"
    ls -1 "$TESTS_DIR"/*.py 2>/dev/null | xargs -I {} basename {} | grep -v __pycache__ | grep -v __init__ || echo "  (no wrappers yet)"
    echo ""
    echo "Available suite tests:"
    ls -1 "$SUITES_DIR"/*.py 2>/dev/null | xargs -I {} basename {} | grep -v __pycache__ | grep -v __init__ || echo "  (no suites yet)"
    exit 0
fi

# Check for test file in wrappers first, then suites
TEST_FILE=""
TEST_TYPE=""

if [ -f "$TESTS_DIR/${FEATURE}_test.py" ]; then
    TEST_FILE="$TESTS_DIR/${FEATURE}_test.py"
    TEST_TYPE="wrapper"
elif [ -f "$SUITES_DIR/test_${FEATURE}.py" ]; then
    TEST_FILE="$SUITES_DIR/test_${FEATURE}.py"
    TEST_TYPE="suite"
else
    echo -e "${RED}✗ Test file not found for: $FEATURE${NC}"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          CloudTester - Wrapper Test Suite${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Testing: $FEATURE ($TEST_TYPE)${NC}"
echo -e "File: $TEST_FILE"
echo "API URL: $TEST_API_URL"
echo ""
echo "Test Configuration:"
echo "  API Tests: $([ "$API_ENABLED" = true ] && echo "Enabled ✅" || echo "Disabled ⏭️ ")"
echo "  GCloud Tests: $([ "$GCLOUD_ENABLED" = true ] && echo "Enabled ☁️ " || echo "Disabled ⏭️ ")"
echo ""

# Create reports directory
mkdir -p "$REPORTS_DIR"

# Build pytest command
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$REPORTS_DIR/wrapper-${FEATURE}-${TIMESTAMP}.html"

PYTEST_ARGS="-v --tb=short --strict-markers -s"
PYTEST_ARGS="$PYTEST_ARGS --html=$REPORT_FILE --self-contained-html"

# Set environment variables for test controls
export ENABLE_GCLOUD_TESTS=$GCLOUD_ENABLED
export ENABLE_API_TESTS=$API_ENABLED

echo -e "${YELLOW}Starting test execution...${NC}"
echo ""
# Run the tests
cd "$PROJECT_ROOT"

pytest "$TEST_FILE" $PYTEST_ARGS 2>&1 | tee /tmp/wrapper_test_output.txt

TEST_RESULT=${PIPESTATUS[0]}

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}║✓ All tests PASSED${NC}"
else
    echo -e "${RED}║✗ Some tests FAILED${NC}"
    echo -e "${RED}║${NC}"
    echo -e "${RED}║ Failed tests summary:${NC}"
    grep -E "FAILED|ERROR" /tmp/wrapper_test_output.txt | head -10 || true
fi
echo -e "${BLUE}║${NC}"
echo -e "${BLUE}║ 📊 Test Report:${NC}"
echo -e "${BLUE}║   $REPORT_FILE${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${CYAN}✅ Test report generated at: $REPORT_FILE${NC}"
echo ""

exit $TEST_RESULT