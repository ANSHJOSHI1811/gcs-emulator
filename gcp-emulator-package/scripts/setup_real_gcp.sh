#!/usr/bin/env bash
set -euo pipefail

echo "Reverting environment to Real GCP"

unset STORAGE_EMULATOR_HOST || true
unset CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE || true
unset BOTO_CONFIG || true

gcloud config unset auth/disable_credentials >/dev/null || true

echo "Environment reverted. Run 'gcloud auth login' for real GCP."
