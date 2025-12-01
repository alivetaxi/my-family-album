# Backend (GCP Cloud Functions)

This directory contains a minimal Python Cloud Function implementing a tiny REST API to manage albums and photos. It uses Firestore for metadata and Cloud Storage for images.

Environment variables expected by the function:
- `IMAGES_BUCKET` : name of the Cloud Storage bucket used to store images
- `GCP_PROJECT` or `GOOGLE_CLOUD_PROJECT`: GCP project id (used to access Secret Manager)
- `ALLOWED_ORIGINS`: comma-separated origins allowed for CORS (use specific origins in production)
- `FIREBASE_CLIENT_CONFIG`: optional JSON string with Firebase web config for frontend
- `FIREBASE_API_KEY`, `FIREBASE_AUTH_DOMAIN`, `FIREBASE_PROJECT_ID`, `FIREBASE_APP_ID`: alternative individual client config vars
- `FIREBASE_ADMIN_SECRET_NAME`: optional Secret Manager secret name containing Firebase Admin service account JSON

Deploy example (gcloud):

```bash
# from repo root
gcloud functions deploy api \
  --runtime python311 \
  --trigger-http \
  --entry-point main \
  --region REGION \
  --set-env-vars IMAGES_BUCKET=your-bucket-name
```

Deploy with Terraform (packaging)

If you prefer to package and deploy the Cloud Function with Terraform, set `-var="functions_bucket=your-unique-functions-bucket"` when running `terraform apply` from the `terraform/` folder. Terraform will create a zip from the `backend/` folder, upload it, and create a `google_cloudfunctions_function` resource. See `terraform/README.md` for details.


Notes:
- The function verifies Firebase ID tokens using `firebase_admin`. If `FIREBASE_ADMIN_SECRET_NAME` is set, the function will attempt to read the service account JSON from Secret Manager and initialize `firebase_admin` with those credentials. Otherwise it will use default credentials available to the runtime.
- Make sure the Cloud Function's service account has access to Firestore, Cloud Storage, and (if using Secret Manager) the secret accessor role for the admin secret.
- For local testing, set `GOOGLE_APPLICATION_CREDENTIALS` to a service account key and create a Firebase service account with proper privileges. You can also set the env vars listed above in your shell (see `.env.example`).
