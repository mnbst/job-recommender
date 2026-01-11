# ============================================
# Cloud Load Balancer
# ============================================

# 静的IPアドレス（グローバル）
resource "google_compute_global_address" "lb_ip" {
  name = "job-recommender-lb-ip"

  lifecycle {
    prevent_destroy = true
  }
}

# Serverless NEG
resource "google_compute_region_network_endpoint_group" "cloudrun_neg" {
  name                  = "job-recommender-neg"
  region                = var.region
  network_endpoint_type = "SERVERLESS"

  cloud_run {
    service = google_cloud_run_v2_service.app.name
  }
}

# Backend Service (Blue - Production)
resource "google_compute_backend_service" "app" {
  name                  = "job-recommender-backend"
  protocol              = "HTTPS"
  port_name             = "http"
  timeout_sec           = 30
  enable_cdn            = false
  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group = google_compute_region_network_endpoint_group.cloudrun_neg.id
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

# URL Map
resource "google_compute_url_map" "app" {
  name            = "job-recommender-url-map"
  default_service = google_compute_backend_service.app.id
}

# SSL証明書（Google管理）
resource "google_compute_managed_ssl_certificate" "app" {
  name = var.domain_name != "" ? "job-recommender-cert-custom" : "job-recommender-cert-nipio"

  managed {
    domains = var.domain_name != "" ? (
      var.www_domain_name != "" ? [var.domain_name, var.www_domain_name] : [var.domain_name]
    ) : ["${google_compute_global_address.lb_ip.address}.nip.io"]
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Target HTTPS Proxy
resource "google_compute_target_https_proxy" "app" {
  name             = "job-recommender-https-proxy"
  url_map          = google_compute_url_map.app.id
  ssl_certificates = [google_compute_managed_ssl_certificate.app.id]
}

# HTTPS Forwarding Rule
resource "google_compute_global_forwarding_rule" "https" {
  name                  = "job-recommender-https-rule"
  ip_protocol           = "TCP"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  port_range            = "443"
  target                = google_compute_target_https_proxy.app.id
  ip_address            = google_compute_global_address.lb_ip.id
}

# HTTP to HTTPS リダイレクト
resource "google_compute_url_map" "http_redirect" {
  name = "job-recommender-http-redirect"

  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    strip_query            = false
  }
}

resource "google_compute_target_http_proxy" "redirect" {
  name    = "job-recommender-http-proxy"
  url_map = google_compute_url_map.http_redirect.id
}

resource "google_compute_global_forwarding_rule" "http" {
  name                  = "job-recommender-http-rule"
  ip_protocol           = "TCP"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  port_range            = "80"
  target                = google_compute_target_http_proxy.redirect.id
  ip_address            = google_compute_global_address.lb_ip.id
}

# ============================================
# Outputs
# ============================================

output "load_balancer_ip" {
  description = "Load Balancer IP address"
  value       = google_compute_global_address.lb_ip.address
}

output "load_balancer_url" {
  description = "Load Balancer URL"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "https://${google_compute_global_address.lb_ip.address}.nip.io"
}

output "artifact_registry_url" {
  description = "Artifact Registry URL for docker push"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}"
}
