terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# プロジェクト情報を取得（プロジェクトNumberを動的に取得するため）
data "google_project" "project" {
  project_id = var.project_id
}
