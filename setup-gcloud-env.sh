#!/bin/bash
#
# GCP Stimulator Environment Setup
# Source this file to configure gcloud CLI to use local GCP Stimulator
#
# Usage:
#   source setup-gcloud-env.sh
#   OR
#   . setup-gcloud-env.sh
#

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}    GCP Stimulator - gcloud CLI Environment Setup${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Set GCP Stimulator endpoint overrides
export CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE="http://localhost:8080/storage/v1/"
export CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE="http://localhost:8080/compute/v1/"
export CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM="http://localhost:8080/iam/"
export CLOUDSDK_CORE_PROJECT="test-project"

# Disable SSL verification for local testing
export CLOUDSDK_CORE_DISABLE_PROMPTS="1"
export CLOUDSDK_PYTHON_SITEPACKAGES="1"

# For Python SDK
export STORAGE_EMULATOR_HOST="http://localhost:8080"

echo -e "${GREEN}✓${NC} Environment variables configured:"
echo ""
echo -e "  ${YELLOW}CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE${NC} = $CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE"
echo -e "  ${YELLOW}CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE${NC} = $CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE"
echo -e "  ${YELLOW}CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM${NC}     = $CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM"
echo -e "  ${YELLOW}CLOUDSDK_CORE_PROJECT${NC}                   = $CLOUDSDK_CORE_PROJECT"
echo -e "  ${YELLOW}STORAGE_EMULATOR_HOST${NC}                   = $STORAGE_EMULATOR_HOST"
echo ""
echo -e "${GREEN}✓${NC} gcloud CLI is now configured to use GCP Stimulator at localhost:8080"
echo ""
echo -e "${BLUE}You can now run gcloud commands directly:${NC}"
echo -e "  ${YELLOW}gcloud storage buckets list${NC}"
echo -e "  ${YELLOW}gcloud compute zones list${NC}"
echo -e "  ${YELLOW}gcloud compute networks list${NC}"
echo -e "  ${YELLOW}gcloud iam service-accounts list${NC}"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
