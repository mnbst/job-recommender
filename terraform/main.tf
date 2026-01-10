# ============================================
# Artifact Registry
# ============================================
resource "google_artifact_registry_repository" "app" {
  repository_id = "job-recommender"
  format        = "DOCKER"
  location      = var.region
  description   = "Docker images for Job Recommender"

  lifecycle {
    prevent_destroy = true
  }
}

# ============================================
# Secret Manager（既存シークレットを参照）
# ============================================
data "google_secret_manager_secret" "github_token" {
  secret_id = "github_token"
}

data "google_secret_manager_secret" "perplexity" {
  secret_id = "perplexity_api_key"
}

data "google_secret_manager_secret" "github_oauth_client_id" {
  secret_id = "github_oauth_client_id"
}

data "google_secret_manager_secret" "github_oauth_client_secret" {
  secret_id = "github_oauth_client_secret"
}

data "google_secret_manager_secret" "green_github_oauth_client_id" {
  secret_id = "green_github_oauth_client_id"
}

data "google_secret_manager_secret" "green_github_oauth_client_secret" {
  secret_id = "green_github_oauth_client_secret"
}
# ============================================
# Service Account
# ============================================
resource "google_service_account" "app" {
  account_id   = "job-recommender-sa"
  display_name = "Service Account for Job Recommender Cloud Run"
}

# Secret Managerへのアクセス権限 (GitHub Token)
resource "google_secret_manager_secret_iam_member" "github_token_access" {
  secret_id = data.google_secret_manager_secret.github_token.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app.email}"
}

# Secret Managerへのアクセス権限 (Perplexity)
resource "google_secret_manager_secret_iam_member" "perplexity_access" {
  secret_id = data.google_secret_manager_secret.perplexity.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app.email}"
}

# Secret Managerへのアクセス権限 (GitHub OAuth Client ID)
resource "google_secret_manager_secret_iam_member" "github_oauth_client_id_access" {
  secret_id = data.google_secret_manager_secret.github_oauth_client_id.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app.email}"
}

# Secret Managerへのアクセス権限 (GitHub OAuth Client Secret)
resource "google_secret_manager_secret_iam_member" "github_oauth_client_secret_access" {
  secret_id = data.google_secret_manager_secret.github_oauth_client_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app.email}"
}

resource "google_secret_manager_secret_iam_member" "green_github_oauth_client_id_access" {
  secret_id = data.google_secret_manager_secret.green_github_oauth_client_id.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app.email}"
}

resource "google_secret_manager_secret_iam_member" "green_github_oauth_client_secret_access" {
  secret_id = data.google_secret_manager_secret.green_github_oauth_client_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app.email}"
}

# Vertex AI へのアクセス権限
resource "google_project_iam_member" "app_vertex_ai" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.app.email}"
}


# ============================================
# Cloud Run
# ============================================
resource "google_cloud_run_v2_service" "app" {
  name                = "job-recommender"
  location            = var.region
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = google_service_account.app.email

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}/app:latest"

      ports {
        container_port = 8501
      }

      resources {
        limits = {
          cpu    = "1000m"
          memory = "1Gi"
        }
      }

      env {
        name  = "PYTHONUNBUFFERED"
        value = "1"
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "GCP_LOCATION"
        value = var.region
      }

      env {
        name = "GITHUB_TOKEN"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.github_token.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "PERPLEXITY_API_KEY"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.perplexity.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "GITHUB_OAUTH_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.github_oauth_client_id.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "GITHUB_OAUTH_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.github_oauth_client_secret.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "OAUTH_REDIRECT_URI"
        value = var.domain_name != "" ? "https://${var.domain_name}" : "https://${google_compute_global_address.lb_ip.address}.nip.io"
      }
    }

    max_instance_request_concurrency = 80
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

}

resource "google_cloud_run_v2_service" "green" {
  name                = "job-recommender-green"
  location            = var.region
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.app.email

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}/app:latest"

      ports {
        container_port = 8501
      }

      resources {
        limits = {
          cpu    = "1000m"
          memory = "1Gi"
        }
      }

      env {
        name  = "PYTHONUNBUFFERED"
        value = "1"
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "GCP_LOCATION"
        value = var.region
      }

      env {
        name = "GITHUB_TOKEN"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.github_token.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "PERPLEXITY_API_KEY"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.perplexity.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "GITHUB_OAUTH_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.green_github_oauth_client_id.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "GITHUB_OAUTH_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.green_github_oauth_client_secret.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "OAUTH_REDIRECT_URI"
        value = var.domain_name != "" ? "https://${var.domain_name}" : "https://${google_compute_global_address.lb_ip.address}.nip.io"
      }
    }

    max_instance_request_concurrency = 80
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# ============================================
# Cloud Run IAM
# ============================================
# Cloud Run Invoker (public - blue)
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Run Invoker (restricted - green)
resource "google_cloud_run_v2_service_iam_member" "green_invokers" {
  for_each = toset(var.cloud_run_invoker_members)

  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.green.name
  role     = "roles/run.invoker"
  member   = each.value
}

# ============================================
# Audit Logs
# ============================================
resource "google_project_iam_audit_config" "cloud_run_logs" {
  project = var.project_id
  service = "run.googleapis.com"

  audit_log_config {
    log_type = "ADMIN_READ"
  }
  audit_log_config {
    log_type = "DATA_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}
