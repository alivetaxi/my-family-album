output "images_bucket" {
  value = google_storage_bucket.images.name
}

output "functions_service_account_email" {
  value = google_service_account.functions_sa.email
}
