#!/bin/bash
# CloudTester - Wrapper Test Runner
# Runs tests for a specific feature during development
# Usage: ./tests/run_wrapper_tests.sh [feature_name]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TESTS_DIR="$SCRIPT_DIR/CloudTester/wrappers"
ENV_FILE="$SCRIPT_DIR/.env-test"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load environment
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

# Get feature name from argument
FEATURE=${1:-""}

if [ -z "$FEATURE" ]; then
    echo -e "${YELLOW}Usage: ./run_wrapper_tests.sh [feature_name]${NC}"
    echo ""
    echo "Examples:"
    echo "  ./run_wrapper_tests.sh firewall"
    echo "  ./run_wrapper_tests.sh compute"
    echo ""
    echo "Available wrapper tests:"
    ls -1 "$TESTS_DIR"/*.py 2>/dev/null | xargs -I {} basename {} | grep -v __pycache__ || echo "  (no wrappers yet)"
    exit 0
fi

TEST_FILE="$TESTS_DIR/${FEATURE}_test.py"

if [ ! -f "$TEST_FILE" ]; then
    echo -e "${RED}✗ Test file not found: $TEST_FILE${NC}"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          CloudTester - Wrapper Test Suite${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Testing: $FEATURE${NC}"
echo -e "File: $TEST_FILE"
echo "API URL: $TEST_API_URL"
echo ""

# Run the tests
cd "$PROJECT_ROOT"

pytest "$TEST_FILE" \
    -v \
    --tb=short \
    --strict-markers \
    -s \
    2>&1 | tee /tmp/wrapper_test_output.txt

TEST_RESULT=${PIPESTATUS[0]}

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}║✓ Wrapper tests PASSED${NC}"
else
    echo -e "${RED}║✗ Wrapper tests FAILED${NC}"
fi
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"

exit $TEST_RESULT
