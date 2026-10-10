#!/usr/bin/env bash
# =============================================================================
# Grubhub Merchant Menu Image Platform - One-Shot Cloud Deployment Script
# =============================================================================
# This script provisions Google Cloud infrastructure using Terraform, builds
# and pushes the container image via Cloud Build, and deploys the live demo
# microservice on Google Cloud Run.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# -----------------------------------------------------------------------------
# Configuration & Defaults
# -----------------------------------------------------------------------------
if [ -f "${SCRIPT_DIR}/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "${SCRIPT_DIR}/.env"
    set +a
fi

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null || echo "")}"
if [ -z "${PROJECT_ID}" ] || [ "${PROJECT_ID}" = "your-gcp-project-id" ]; then
    echo "❌ Error: GOOGLE_CLOUD_PROJECT is not set. Export GOOGLE_CLOUD_PROJECT or configure it in .env." >&2
    exit 1
fi
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
REPO_NAME="${ARTIFACT_REPO_NAME:-grubhub-merchant}"
SERVICE_NAME="${SERVICE_NAME:-grubhub-merchant-platform}"
IMAGE_TAG="${IMAGE_TAG:-$(date +%Y%m%d-%H%M%S)}"
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/app:${IMAGE_TAG}"

# Ensure terraform binary is found
if command -v terraform >/dev/null 2>&1; then
    TERRAFORM_CMD="terraform"
elif [ -x "${HOME}/.local/bin/terraform" ]; then
    TERRAFORM_CMD="${HOME}/.local/bin/terraform"
elif [ -x "/usr/local/bin/terraform" ]; then
    TERRAFORM_CMD="/usr/local/bin/terraform"
else
    echo "❌ Error: 'terraform' executable not found in PATH or ~/.local/bin." >&2
    exit 1
fi

# Ensure gcloud binary is found
if command -v gcloud >/dev/null 2>&1; then
    GCLOUD_CMD="gcloud"
elif [ -x "/usr/bin/gcloud" ]; then
    GCLOUD_CMD="/usr/bin/gcloud"
else
    echo "❌ Error: 'gcloud' executable not found." >&2
    exit 1
fi

echo "================================================================================"
echo "🚀 Deploying Grubhub Merchant Menu Platform Demo to Google Cloud"
echo "================================================================================"
echo "Project ID  : ${PROJECT_ID}"
echo "Region      : ${REGION}"
echo "Artifact Repo: ${REPO_NAME}"
echo "Service Name: ${SERVICE_NAME}"
echo "Image URI   : ${IMAGE_URI}"
echo "Terraform   : $(${TERRAFORM_CMD} version -json | grep -o '\"version\":[^,]*' || echo 'available')"
echo "================================================================================"

# -----------------------------------------------------------------------------
# Step 1: Initialize Terraform
# -----------------------------------------------------------------------------
echo ""
echo "📦 [Step 1/4] Initializing Terraform in terraform/..."
"${TERRAFORM_CMD}" -chdir=terraform init

# -----------------------------------------------------------------------------
# Step 2: Bootstrap APIs & Artifact Registry Repository
# -----------------------------------------------------------------------------
echo ""
echo "🏗️  [Step 2/4] Provisioning GCP APIs and Artifact Registry Repository..."
"${TERRAFORM_CMD}" -chdir=terraform apply \
    -var="project_id=${PROJECT_ID}" \
    -var="region=${REGION}" \
    -var="artifact_repo_name=${REPO_NAME}" \
    -var="service_name=${SERVICE_NAME}" \
    -var="image_tag=${IMAGE_TAG}" \
    -target=google_project_service.enabled_apis \
    -target=google_artifact_registry_repository.merchant_repo \
    -auto-approve

# -----------------------------------------------------------------------------
# Step 3: Build & Push Container Image via Cloud Build
# -----------------------------------------------------------------------------
echo ""
echo "🔨 [Step 3/4] Building container image with Google Cloud Build & pushing to Artifact Registry..."
"${GCLOUD_CMD}" builds submit \
    --project="${PROJECT_ID}" \
    --tag="${IMAGE_URI}" \
    .

echo "🏷️  Tagging ${IMAGE_URI} as :latest in Artifact Registry..."
"${GCLOUD_CMD}" artifacts docker tags add \
    "${IMAGE_URI}" \
    "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/app:latest" \
    --quiet || true

# -----------------------------------------------------------------------------
# Step 4: Apply Full Terraform Infrastructure (Cloud Run, GCS, IAM, Ingress)
# -----------------------------------------------------------------------------
echo ""
echo "☁️  [Step 4/4] Deploying Cloud Run microservice and GCS storage ledger..."
"${TERRAFORM_CMD}" -chdir=terraform apply \
    -var="project_id=${PROJECT_ID}" \
    -var="region=${REGION}" \
    -var="artifact_repo_name=${REPO_NAME}" \
    -var="service_name=${SERVICE_NAME}" \
    -var="image_tag=${IMAGE_TAG}" \
    -auto-approve

# -----------------------------------------------------------------------------
# Completion Summary
# -----------------------------------------------------------------------------
CLOUD_RUN_URL=$("${TERRAFORM_CMD}" -chdir=terraform output -raw cloud_run_url 2>/dev/null || echo "")
GCS_BUCKET=$("${TERRAFORM_CMD}" -chdir=terraform output -raw gcs_bucket_name 2>/dev/null || echo "")
SA_EMAIL=$("${TERRAFORM_CMD}" -chdir=terraform output -raw service_account_email 2>/dev/null || echo "")

echo ""
echo "================================================================================"
echo "✅ Deployment Successful!"
echo "================================================================================"
if [ -n "${CLOUD_RUN_URL}" ]; then
    echo "🌐 Demo Web UI URL    : ${CLOUD_RUN_URL}"
fi
if [ -n "${GCS_BUCKET}" ]; then
    echo "🪣 Asset Storage Bucket: gs://${GCS_BUCKET}"
fi
if [ -n "${SA_EMAIL}" ]; then
    echo "🔑 Service Account     : ${SA_EMAIL}"
fi
echo "================================================================================"
echo "You can now open the Web UI URL to test image inspection, Studio Reshoot bypass,"
echo "and enhancement live in Google Cloud!"
echo "================================================================================"
