#!/usr/bin/env bash
set -euo pipefail

PROJECT=${1:-test-project}
ZONE=${2:-us-central1-a}

echo "Setting up emulator environment for gcloud + gsutil"

export STORAGE_EMULATOR_HOST=http://localhost:8080
export CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE=http://localhost:8080/compute/v1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS_DIR="${SCRIPT_DIR}/../docs"
export BOTO_CONFIG="${DOCS_DIR}/gsutil-emulator.boto"

gcloud config set core/project "$PROJECT" >/dev/null
gcloud config set compute/zone "$ZONE" >/dev/null
gcloud config set auth/disable_credentials true >/dev/null

echo "Emulator setup complete"
echo "- STORAGE_EMULATOR_HOST=${STORAGE_EMULATOR_HOST}"
echo "- CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE=${CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE}"
echo "- BOTO_CONFIG=${BOTO_CONFIG}"
echo "Try: gsutil ls   |   gcloud compute instances list"
