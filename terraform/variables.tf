variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
  default     = "your-gcp-project-id"

  validation {
    condition     = length(trimspace(var.project_id)) > 0 && var.project_id != "your-gcp-project-id"
    error_message = "A valid Google Cloud project_id must be specified via terraform/terraform.tfvars or -var=\"project_id=...\"."
  }
}

variable "region" {
  description = "The primary Google Cloud region for compute and storage resources"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
  default     = "grubhub-merchant-platform"
}

variable "artifact_repo_name" {
  description = "Artifact Registry Docker repository name"
  type        = string
  default     = "grubhub-merchant"
}

variable "image_tag" {
  description = "Container image tag to deploy to Cloud Run"
  type        = string
  default     = "latest"
}

variable "min_instances" {
  description = "Minimum warm instances for Cloud Run to prevent cold starts"
  type        = number
  default     = 1
}

variable "max_instances" {
  description = "Maximum instances for Cloud Run autoscaling"
  type        = number
  default     = 10
}
