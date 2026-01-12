# ============================================
# Cloud Build Monitoring Alerts
# ============================================

# メール通知チャンネル
resource "google_monitoring_notification_channel" "email" {
  count        = var.alert_email != "" ? 1 : 0
  display_name = "Build Alert Email"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }
}

# ビルド成功アラート（ログベース）
resource "google_monitoring_alert_policy" "build_success" {
  count        = var.alert_email != "" ? 1 : 0
  display_name = "Cloud Build Success"
  combiner     = "OR"

  conditions {
    display_name = "Build completed successfully"

    condition_matched_log {
      filter = <<-EOT
        resource.type="build"
        logName="projects/${var.project_id}/logs/cloudbuild"
        textPayload="DONE"
      EOT
    }
  }

  notification_channels = [google_monitoring_notification_channel.email[0].id]

  alert_strategy {
    notification_rate_limit {
      period = "300s"
    }
    auto_close = "604800s"
  }

  documentation {
    content   = "Cloud Build completed successfully.\n\nProject: ${var.project_id}"
    mime_type = "text/markdown"
  }
}

# ビルド失敗アラート（ログベース）
resource "google_monitoring_alert_policy" "build_failure" {
  count        = var.alert_email != "" ? 1 : 0
  display_name = "Cloud Build Failure"
  combiner     = "OR"

  conditions {
    display_name = "Build failed"

    condition_matched_log {
      filter = <<-EOT
        resource.type="build"
        logName="projects/${var.project_id}/logs/cloudbuild"
        textPayload="ERROR"
      EOT
    }
  }

  notification_channels = [google_monitoring_notification_channel.email[0].id]

  alert_strategy {
    notification_rate_limit {
      period = "300s"
    }
    auto_close = "604800s"
  }

  documentation {
    content   = "Cloud Build FAILED!\n\nProject: ${var.project_id}\n\nCheck the build logs in GCP Console."
    mime_type = "text/markdown"
  }
}
