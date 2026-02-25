#!/bin/bash
# Promotion Script - Moves tests from wrapper (development) to stable (production)
# Usage: ./promote_to_stable.sh <service_name>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
WRAPPERS_DIR="$SCRIPT_DIR/../wrappers"
INTEGRATION_DIR="$SCRIPT_DIR/../suites/integration"

SERVICE=${1:-""}

if [ -z "$SERVICE" ]; then
    echo "❌ Usage: $0 <service_name>"
    exit 1
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Promoting $SERVICE tests to Stable${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if wrapper tests exist
API_TEST="$WRAPPERS_DIR/test_${SERVICE}_api_dev.py"
GCLOUD_TEST="$WRAPPERS_DIR/test_${SERVICE}_gcloud_dev.py"

if [ ! -f "$API_TEST" ] && [ ! -f "$GCLOUD_TEST" ]; then
    echo -e "${RED}❌ No wrapper tests found for $SERVICE${NC}"
    echo "   Expected: $API_TEST or $GCLOUD_TEST"
    exit 1
fi

# Create integration directory if it doesn't exist
mkdir -p "$INTEGRATION_DIR"

# Move API test
if [ -f "$API_TEST" ]; then
    STABLE_API="$INTEGRATION_DIR/test_${SERVICE}_api.py"
    echo "📦 Promoting API tests..."
    cp "$API_TEST" "$STABLE_API"
    
    # Remove "Development" status from docstring
    sed -i 's/Status: 🧪 Experimental/Status: ✅ Stable/g' "$STABLE_API"
    
    echo -e "${GREEN}✅ $STABLE_API${NC}"
fi

# Move gcloud test
if [ -f "$GCLOUD_TEST" ]; then
    STABLE_GCLOUD="$INTEGRATION_DIR/test_${SERVICE}_gcloud.py"
    echo "📦 Promoting gcloud tests..."
    cp "$GCLOUD_TEST" "$STABLE_GCLOUD"
    
    # Remove "Development" status from docstring
    sed -i 's/Status: 🧪 Experimental/Status: ✅ Stable/g' "$STABLE_GCLOUD"
    
    echo -e "${GREEN}✅ $STABLE_GCLOUD${NC}"
fi

echo ""
echo -e "${YELLOW}Running regression check...${NC}"
echo ""

# Run stable suite to check for regressions
cd "$PROJECT_ROOT"
if ./tests/run_full_suite.sh --marker integration; then
    echo ""
    echo -e "${GREEN}✅ No regressions detected!${NC}"
    echo ""
    echo -e "${BLUE}Promotion successful! Tests are now stable.${NC}"
    echo ""
    echo "📝 Next steps:"
    echo "  1. Review changes"
    echo "  2. Commit with: git add . && git commit -m 'feat: add $SERVICE tests'"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Regression detected!${NC}"
    echo "   Fix the failing tests and try again."
    exit 1
fi
