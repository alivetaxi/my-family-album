terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "storage" {
  service = "storage.googleapis.com"
}
resource "google_project_service" "firestore" {
  service = "firestore.googleapis.com"
}
resource "google_project_service" "firebase" {
  service = "firebase.googleapis.com"
}
resource "google_project_service" "firebasehosting" {
  service = "firebasehosting.googleapis.com"
}
resource "google_project_service" "functions" {
  service = "cloudfunctions.googleapis.com"
}
resource "google_project_service" "iam" {
  service = "iam.googleapis.com"
}

resource "google_project_service" "iamcredentials" {
  service = "iamcredentials.googleapis.com"
}

resource "google_storage_bucket" "images" {
  name     = var.images_bucket
  location = var.region
  uniform_bucket_level_access = true
  force_destroy = true
}

resource "google_storage_bucket" "logs" {
  name     = var.logs_bucket
  location = var.region
  uniform_bucket_level_access = true
  force_destroy = true
}

resource "google_service_account" "functions_sa" {
  account_id   = "my-family-album-fn-sa"
  display_name = "Service account for Cloud Functions"
}

// Allow the functions service account to access Firestore and Storage at project level (minimum set)
resource "google_project_iam_member" "functions_datastore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.functions_sa.email}"
}

resource "google_project_iam_member" "functions_storage_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.functions_sa.email}"
}

resource "google_project_iam_member" "functions_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.functions_sa.email}"
}

resource "google_project_iam_member" "functions_sa_token_creator" {
  project = var.project_id
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = "serviceAccount:${google_service_account.functions_sa.email}"
}

resource "google_service_account_iam_member" "functions_sa_token_creator_self_binding" {
  service_account_id = google_service_account.functions_sa.id
  role = "roles/iam.serviceAccountTokenCreator"
  member = "serviceAccount:${google_service_account.functions_sa.email}"
}

// Create Firestore database in Native mode
resource "google_firestore_database" "default" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

// Register the GCP project with Firebase (required for Hosting and some Firebase services)
resource "google_firebase_project" "firebase_project" {
  provider = google-beta
  project  = var.project_id
}
