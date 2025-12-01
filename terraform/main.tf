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

resource "google_storage_bucket" "images" {
  name     = var.images_bucket
  location = var.region
  uniform_bucket_level_access = true
  force_destroy = true
}

// optional bucket to store function source archives
resource "google_storage_bucket" "functions_source" {
  count    = var.functions_bucket != "" ? 1 : 0
  name     = var.functions_bucket
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

resource "google_storage_bucket_iam_member" "functions_writer" {
  bucket = google_storage_bucket.images.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.functions_sa.email}"
}

// Note: Secret Manager secret creation for Firebase Admin credentials is intentionally omitted here
// because different projects and workflows may want to create and manage secrets manually.
// To use a secret for Firebase Admin credentials, create a secret in Secret Manager named
// something like `firebase-admin-key` and add a secret version containing the service account JSON.
// Then set the Cloud Function env var `FIREBASE_ADMIN_SECRET_NAME` to that secret id.

// Package backend source into a zip archive and upload to functions source bucket
data "archive_file" "function_zip" {
  type        = "zip"
  source_dir  = "${path.module}/${var.function_source_dir}"
  output_path = "${path.module}/function-${var.function_name}.zip"
}

resource "google_storage_bucket_object" "function_archive" {
  count = var.functions_bucket != "" ? 1 : 0
  name   = "${var.function_name}.zip"
  bucket = google_storage_bucket.functions_source[0].name
  source = data.archive_file.function_zip.output_path
  depends_on = [google_storage_bucket.functions_source]
}

resource "google_cloudfunctions_function" "api" {
  count = var.functions_bucket != "" ? 1 : 0
  name        = var.function_name
  runtime     = var.function_runtime
  entry_point = var.function_entry_point
  region      = var.region
  source_archive_bucket = google_storage_bucket.functions_source[0].name
  source_archive_object = google_storage_bucket_object.function_archive[0].name
  trigger_http = true
  available_memory_mb = 256
  service_account_email = google_service_account.functions_sa.email
  environment_variables = var.function_env_vars
  depends_on = [google_storage_bucket_object.function_archive]
}

resource "google_cloudfunctions_function_iam_member" "invoker" {
  count = var.functions_bucket != "" ? 1 : 0
  project = var.project_id
  region  = var.region
  cloud_function = google_cloudfunctions_function.api[0].name
  role   = "roles/cloudfunctions.invoker"
  member = "allUsers"
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
