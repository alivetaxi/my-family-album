output "images_bucket" {
  value = google_storage_bucket.images.name
}

output "functions_service_account_email" {
  value = google_service_account.functions_sa.email
}


output "function_url" {
  value = length(google_cloudfunctions_function.api) > 0 ? google_cloudfunctions_function.api[0].https_trigger_url : ""
  description = "HTTPS trigger URL for the deployed Cloud Function (empty if not created)."
}
