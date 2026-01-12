variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "Region for resources"
  type        = string
  default     = "asia-northeast1"
}

variable "domain_name" {
  description = "Custom domain name for the load balancer (optional, leave empty to use nip.io)"
  type        = string
  default     = ""
}

variable "www_domain_name" {
  description = "WWW subdomain (optional)"
  type        = string
  default     = ""
}

# ============================================
# Cloud Build Variables
# ============================================
variable "cloudbuild_repository_id" {
  description = "Full repository ID from Cloud Build (format: projects/{project}/locations/{region}/connections/{connection}/repositories/{repo})"
  type        = string
}

# ============================================
# Cloud Run IAM
# ============================================
variable "cloud_run_invoker_members" {
  description = "Members allowed to invoke Cloud Run (e.g. user:alice@gmail.com)"
  type        = list(string)
  default     = []
}

# ============================================
# Monitoring Variables
# ============================================
variable "alert_email" {
  description = "Email address for build notifications"
  type        = string
  default     = ""
}
