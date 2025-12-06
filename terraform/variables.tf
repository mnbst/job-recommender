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

variable "iap_support_email" {
  description = "Support email for IAP OAuth consent screen (required)"
  type        = string
}

variable "domain_name" {
  description = "Custom domain name for the load balancer (optional, leave empty to use nip.io)"
  type        = string
  default     = ""
}

