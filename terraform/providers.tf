terraform {
  required_version = ">= 1.6.0"

  backend "gcs" {
    # bucket は terraform init 時に指定:
    # terraform init -backend-config="bucket=${PROJECT_ID}-tfstate"
    prefix = "job-recommender"
  }

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
