variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "images_bucket" {
  description = "Name of the Cloud Storage bucket to store images"
  type        = string
}

variable "firebase_display_name" {
  description = "Optional display name for Firebase project registration"
  type        = string
  default     = "my-family-album"
}

variable "firebase_admin_secret_id" {
  description = "Secret Manager secret id to store Firebase admin key (will be created)."
  type        = string
  default     = "firebase-admin-key"
}

variable "firebase_admin_key_file" {
  description = "Path to Firebase admin service account JSON file to populate Secret Manager (used by Terraform)."
  type        = string
  default     = ""
}

variable "logs_bucket" {
  description = "GCS bucket name used to store cloudbuild logs. Must be globally unique."
  type        = string
  default     = ""
}
