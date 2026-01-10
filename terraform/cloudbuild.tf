# ============================================
# Cloud Build Trigger
# ============================================
# 事前に GCP Console で GitHub 接続を作成してください:
# 1. GCP Console > Cloud Build > Repositories > 2nd gen
# 2. "Create host connection" → GitHub を選択して認証
# 3. "Link repository" でリポジトリをリンク
# 4. リンクしたリポジトリの詳細ページでリポジトリIDをコピー
#    (形式: projects/{project}/locations/{region}/connections/{connection}/repositories/{repo})

# Blue環境（本番）: mainブランチにマージ時
resource "google_cloudbuild_trigger" "main_push" {
  name        = "job-recommender-main-push"
  description = "Deploy to production (blue) on main branch push"
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

# Green環境（検証）: devブランチにプッシュ時
resource "google_cloudbuild_trigger" "dev_push" {
  name        = "job-recommender-dev-push"
  description = "Deploy to staging (green) on dev branch push"
  location    = var.region

  repository_event_config {
    repository = var.cloudbuild_repository_id
    push {
      branch = "^dev$"
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

# Compute Engine サービスアカウント（Cloud Buildトリガーで使用）にロギング権限を付与
resource "google_project_iam_member" "cloudbuild_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Compute Engine サービスアカウントに Cloud Run デプロイ権限を付与
resource "google_project_iam_member" "cloudbuild_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Compute Engine サービスアカウントにサービスアカウント利用権限を付与
resource "google_project_iam_member" "cloudbuild_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}
