output "cloud_run_url" {
  description = "The public HTTPS URL to access the Grubhub Merchant Menu Platform demo web UI"
  value       = google_cloud_run_v2_service.platform_service.uri
}

output "gcs_bucket_name" {
  description = "Google Cloud Storage bucket for persistent assets and serverless ledger"
  value       = google_storage_bucket.assets_bucket.name
}

output "artifact_registry_repo" {
  description = "Artifact Registry repository for container images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo_name}"
}

output "service_account_email" {
  description = "Dedicated Service Account used by Cloud Run"
  value       = google_service_account.platform_sa.email
}
