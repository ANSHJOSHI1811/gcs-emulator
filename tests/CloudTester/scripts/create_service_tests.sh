#!/bin/bash
# Template Generator - Creates test skeleton files for new services
# Usage: ./create_service_tests.sh <service_name>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
WRAPPERS_DIR="$SCRIPT_DIR/../wrappers"
SUITES_DIR="$SCRIPT_DIR/../suites/integration"

SERVICE=${1:-""}

if [ -z "$SERVICE" ]; then
    echo "❌ Usage: $0 <service_name>"
    echo ""
    echo "Examples:"
    echo "  ./create_service_tests.sh gke"
    echo "  ./create_service_tests.sh pubsub"
    echo "  ./create_service_tests.sh cloudrun"
    exit 1
fi

# Create wrappers directory if it doesn't exist
mkdir -p "$WRAPPERS_DIR"
mkdir -p "$SUITES_DIR"

# Convert service name to class name (capitalize each word)
CLASS_NAME=$(echo "$SERVICE" | sed -r 's/(^|-)([a-z])/\U\2/g' | sed 's/-//g')

echo "📝 Creating test templates for service: $SERVICE"
echo ""

# Create API test template
API_TEST_FILE="$WRAPPERS_DIR/test_${SERVICE}_api_dev.py"
cat > "$API_TEST_FILE" << 'EOF'
"""
{{SERVICE}} API Tests (Development)
Status: 🧪 Experimental - Tests can fail during development

These tests validate HTTP API endpoints for {{SERVICE}}.
"""
import pytest
from CloudTester.base import BaseTester


class Test{{CLASS_NAME}}API(BaseTester):
    """Test {{SERVICE}} API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup before each test"""
        self.project = "test-project"
        self.zone = "us-central1-a"
        yield
        # Cleanup after test
        # TODO: Add cleanup logic
    
    def test_create_resource(self):
        """Test: Create {{SERVICE}} resource"""
        # TODO: Implement resource creation test
        # Example:
        # response = self.api.post(
        #     "/path/to/endpoint",
        #     json={"name": "test-resource"}
        # )
        # self.assert_success(response)
        pytest.skip("Not implemented")
    
    def test_list_resources(self):
        """Test: List {{SERVICE}} resources"""
        # TODO: Implement list test
        # Example:
        # response = self.api.get("/path/to/endpoint")
        # self.assert_success(response)
        pytest.skip("Not implemented")
    
    def test_get_resource(self):
        """Test: Get single {{SERVICE}} resource"""
        # TODO: Implement get test
        pytest.skip("Not implemented")
    
    def test_update_resource(self):
        """Test: Update {{SERVICE}} resource"""
        # TODO: Implement update test
        pytest.skip("Not implemented")
    
    def test_delete_resource(self):
        """Test: Delete {{SERVICE}} resource"""
        # TODO: Implement delete test
        pytest.skip("Not implemented")
    
    def test_input_validation(self):
        """Test: Input validation returns 400"""
        # TODO: Test invalid inputs
        pytest.skip("Not implemented")
    
    def test_not_found_returns_404(self):
        """Test: Non-existent resource returns 404"""
        # TODO: Test 404 error
        pytest.skip("Not implemented")
    
    def test_duplicate_returns_409(self):
        """Test: Duplicate resource creation returns 409"""
        # TODO: Test 409 conflict error
        pytest.skip("Not implemented")
EOF

# Replace placeholders
sed -i "s/{{SERVICE}}/$SERVICE/g" "$API_TEST_FILE"
sed -i "s/{{CLASS_NAME}}/$CLASS_NAME/g" "$API_TEST_FILE"

echo "✅ Created: $API_TEST_FILE"

# Create gcloud test template
GCLOUD_TEST_FILE="$WRAPPERS_DIR/test_${SERVICE}_gcloud_dev.py"
cat > "$GCLOUD_TEST_FILE" << 'EOF'
"""
{{SERVICE}} gcloud Tests (Development)
Status: 🧪 Experimental - Tests can fail during development

These tests validate gcloud CLI commands for {{SERVICE}}.
Includes cross-validation with API endpoints.
"""
import pytest
from CloudTester.base import BaseTester


class Test{{CLASS_NAME}}Gcloud(BaseTester):
    """Test {{SERVICE}} via gcloud CLI"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup gcloud environment"""
        # Check if gcloud is available
        self.skip_if_no_gcloud()
        
        self.project = "test-project"
        self.zone = "us-central1-a"
        
        yield
        
        # Cleanup
        # TODO: Add cleanup logic
    
    def test_create_via_gcloud(self):
        """Test: gcloud {{SERVICE}} create"""
        # TODO: Implement gcloud create test
        # Example:
        # result = self.gcloud.run("{{service}} create test-resource --zone=us-central1-a")
        # assert result.is_success()
        pytest.skip("Not implemented")
    
    def test_list_via_gcloud(self):
        """Test: gcloud {{SERVICE}} list"""
        # TODO: Implement gcloud list test
        pytest.skip("Not implemented")
    
    def test_describe_via_gcloud(self):
        """Test: gcloud {{SERVICE}} describe"""
        # TODO: Implement gcloud describe test
        pytest.skip("Not implemented")
    
    def test_delete_via_gcloud(self):
        """Test: gcloud {{SERVICE}} delete"""
        # TODO: Implement gcloud delete test
        pytest.skip("Not implemented")
    
    def test_create_via_api_list_via_gcloud(self):
        """Cross-validation: Create via API, list via gcloud"""
        # TODO: Implement cross-validation test
        # 1. Create resource via API
        # 2. List via gcloud
        # 3. Verify resource appears in gcloud output
        pytest.skip("Not implemented")
    
    def test_create_via_gcloud_get_via_api(self):
        """Cross-validation: Create via gcloud, get via API"""
        # TODO: Implement cross-validation test
        # 1. Create resource via gcloud
        # 2. Get resource via API
        # 3. Verify resource exists with correct properties
        pytest.skip("Not implemented")
    
    def test_gcloud_output_format_json(self):
        """Test: gcloud output format JSON is valid"""
        # TODO: Verify JSON parsing doesn't fail
        pytest.skip("Not implemented")
EOF

# Replace placeholders
sed -i "s/{{SERVICE}}/$SERVICE/g" "$GCLOUD_TEST_FILE"
sed -i "s/{{CLASS_NAME}}/$CLASS_NAME/g" "$GCLOUD_TEST_FILE"

echo "✅ Created: $GCLOUD_TEST_FILE"

echo ""
echo "📋 Next Steps:"
echo "  1. Edit these files and implement the TODO sections:"
echo "     - $API_TEST_FILE"
echo "     - $GCLOUD_TEST_FILE"
echo ""
echo "  2. Run wrapper tests:"
echo "     ./run_wrapper_tests.sh $SERVICE"
echo ""
echo "  3. Fix failures until all tests pass"
echo ""
echo "  4. Promote to stable (when ready):"
echo "     ./promote_to_stable.sh $SERVICE"
echo ""
