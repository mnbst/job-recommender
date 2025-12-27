# ============================================
# Cloud Build Trigger
# ============================================
# 事前に GCP Console で GitHub 接続を作成してください:
# 1. GCP Console > Cloud Build > Repositories > 2nd gen
# 2. "Create host connection" → GitHub を選択して認証
# 3. "Link repository" でリポジトリをリンク
# 4. リンクしたリポジトリの詳細ページでリポジトリIDをコピー
#    (形式: projects/{project}/locations/{region}/connections/{connection}/repositories/{repo})

resource "google_cloudbuild_trigger" "main_push" {
  name        = "job-recommender-main-push"
  description = "Build and push image on main branch push"
  location    = var.region

  repository_event_config {
    repository = var.cloudbuild_repository_id
    push {
      branch = "^main$"
    }
  }

  filename        = "cloudbuild.yaml"
  service_account = "projects/${var.project_id}/serviceAccounts/${data.google_project.project.number}-compute@developer.gserviceaccount.com"

  substitutions = {
    _REGION    = var.region
    _REPO_NAME = google_artifact_registry_repository.app.repository_id
  }
}

# ============================================
# Cloud Build Service Account IAM
# ============================================
# Cloud Build サービスアカウントに Artifact Registry への書き込み権限を付与
resource "google_project_iam_member" "cloudbuild_artifact_registry" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}
