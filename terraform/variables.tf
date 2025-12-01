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

variable "functions_bucket" {
  description = "GCS bucket name used to store function source archives. Must be globally unique."
  type        = string
  default     = ""
}

variable "function_name" {
  description = "Cloud Function name"
  type        = string
  default     = "my-family-album-api"
}

variable "function_runtime" {
  description = "Cloud Function runtime"
  type        = string
  default     = "python311"
}

variable "function_entry_point" {
  description = "Function entry point (callable name)"
  type        = string
  default     = "main"
}

variable "function_source_dir" {
  description = "Path to the function source directory relative to the repo root (used by archive)."
  type        = string
  default     = "../backend"
}

variable "function_env_vars" {
  description = "Map of environment variables to set for the Cloud Function. Do not put secrets here; use Secret Manager."
  type        = map(string)
  default     = {}
}
