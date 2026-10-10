terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.30"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# -----------------------------------------------------------------------------
# 1. Enable Required Google Cloud APIs
# -----------------------------------------------------------------------------
locals {
  services = [
    "run.googleapis.com",              # Cloud Run Admin API
    "artifactregistry.googleapis.com", # Artifact Registry API
    "cloudbuild.googleapis.com",       # Cloud Build API
    "aiplatform.googleapis.com",       # Vertex AI Gemini 3.0+ API
    "storage.googleapis.com",          # Cloud Storage API
    "vision.googleapis.com"            # Cloud Vision API (Crop Hints)
  ]
}

resource "google_project_service" "enabled_apis" {
  for_each           = toset(local.services)
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# -----------------------------------------------------------------------------
# 2. Artifact Registry for Container Images
# -----------------------------------------------------------------------------
resource "google_artifact_registry_repository" "merchant_repo" {
  depends_on    = [google_project_service.enabled_apis]
  project       = var.project_id
  location      = var.region
  repository_id = var.artifact_repo_name
  description   = "Docker repository for Grubhub Merchant Menu Image Platform demo container"
  format        = "DOCKER"
}

# -----------------------------------------------------------------------------
# 3. Google Cloud Storage Bucket for Assets & Serverless Decisions Ledger
# -----------------------------------------------------------------------------
resource "google_storage_bucket" "assets_bucket" {
  depends_on                  = [google_project_service.enabled_apis]
  project                     = var.project_id
  name                        = "${var.project_id}-grubhub-merchant-assets"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
}

# -----------------------------------------------------------------------------
# 4. Dedicated Service Account & Least-Privilege IAM Roles
# -----------------------------------------------------------------------------
resource "google_service_account" "platform_sa" {
  depends_on   = [google_project_service.enabled_apis]
  project      = var.project_id
  account_id   = "grubhub-merchant-sa"
  display_name = "Grubhub Merchant Platform Cloud Run Service Account"
}

# Vertex AI User permission for Gemini 3.8 Flash & Gemini Nano Banana 2.1
resource "google_project_iam_member" "vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.platform_sa.email}"
}

# Service Usage Consumer for Cloud Vision API & Vertex AI consumption
resource "google_project_iam_member" "service_usage_consumer" {
  project = var.project_id
  role    = "roles/serviceusage.serviceUsageConsumer"
  member  = "serviceAccount:${google_service_account.platform_sa.email}"
}

# Cloud Storage Object Admin for reading/writing dishes, enhanced assets & decisions ledger
resource "google_storage_bucket_iam_member" "gcs_admin" {
  bucket = google_storage_bucket.assets_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.platform_sa.email}"
}

# -----------------------------------------------------------------------------
# 5. Cloud Run v2 Microservice (FastAPI + Web UI + AI Studio)
# -----------------------------------------------------------------------------
resource "google_cloud_run_v2_service" "platform_service" {
  depends_on = [
    google_project_service.enabled_apis,
    google_artifact_registry_repository.merchant_repo,
    google_project_iam_member.vertex_user,
    google_storage_bucket_iam_member.gcs_admin
  ]

  name     = var.service_name
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.platform_sa.email
    timeout         = "300s"

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo_name}/app:${var.image_tag}"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = "global"
      }
      env {
        name  = "GCS_ASSETS_BUCKET"
        value = google_storage_bucket.assets_bucket.name
      }
      env {
        name  = "ENABLE_GCS_STORAGE"
        value = "true"
      }
      env {
        name  = "INSPECTION_MODEL"
        value = "gemini-3.8-flash"
      }
      env {
        name  = "AUDITOR_MODEL"
        value = "gemini-3.8-flash"
      }
      env {
        name  = "ENHANCEMENT_MODEL"
        value = "gemini-nano-banana-2.1"
      }
    }
  }
}

# -----------------------------------------------------------------------------
# 6. Public Ingress Access for Frictionless Demo
# -----------------------------------------------------------------------------
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.platform_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
