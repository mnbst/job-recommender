variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "Region for resources"
  type        = string
  default     = "asia-northeast1"
}

variable "authorized_members" {
  description = "List of members authorized to access via IAP (e.g., user:alice@example.com)"
  type        = list(string)
  default     = []
}

variable "iap_oauth2_client_id" {
  description = "OAuth2 Client ID for IAP (create manually in GCP Console)"
  type        = string
}

variable "iap_oauth2_client_secret" {
  description = "OAuth2 Client Secret for IAP (create manually in GCP Console)"
  type        = string
  sensitive   = true
}

variable "domain_name" {
  description = "Custom domain name for the load balancer (optional, leave empty to use nip.io)"
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

