# Terraform

This folder contains a minimal Terraform configuration to create:

- A Cloud Storage bucket for images
- A service account used by Cloud Functions
- Enable required Google APIs

Usage:

```bash
cd terraform
terraform init
terraform apply -var="project_id=YOUR_PROJECT" -var="images_bucket=your-unique-bucket-name"

Notes about Firestore and Firebase Hosting
- This configuration attempts to create a Firestore Native-mode database and register the GCP project with Firebase. Creating Firestore in an existing project may require enabling billing and can take a few minutes.
- Terraform will enable `firebase.googleapis.com` and `firebasehosting.googleapis.com` APIs. To finish Hosting deployment you will typically run `firebase init hosting` locally and deploy with the Firebase CLI.

Example apply with region:

```bash
terraform apply -var="project_id=YOUR_PROJECT" -var="images_bucket=your-unique-bucket-name" -var="region=us-central1"
```

After `terraform apply`:

- Note the `images_bucket` output. Set Cloud Function env var `IMAGES_BUCKET` to that value when deploying the function.
- Initialize Firebase Hosting locally and deploy the `frontend/` folder:

```bash
npm install -g firebase-tools
firebase login
firebase init hosting
# choose the existing project created above
firebase deploy --only hosting
```

Secret Manager info
- To populate the Firebase Admin service account key into Secret Manager via Terraform, set `-var="firebase_admin_key_file=/path/to/key.json"` when you run `terraform apply`. If you omit that variable, Terraform will create the secret resource but not add a secret version.
- After apply, `firebase_admin_secret_id` output contains the secret id. Use that value for `FIREBASE_ADMIN_SECRET_NAME` environment variable when deploying Cloud Functions.

Cloud Functions env var example (gcloud):

```bash
gcloud functions deploy api \
	--runtime python311 \
	--trigger-http \
	--entry-point main \
	--region us-central1 \
	--set-env-vars IMAGES_BUCKET=$(terraform output -raw images_bucket),FIREBASE_ADMIN_SECRET_NAME=$(terraform output -raw firebase_admin_secret_id),ALLOWED_ORIGINS="https://example.com"
```

Packaging & deploying Cloud Function via Terraform

Set `-var="functions_bucket=your-unique-functions-bucket"` and optionally `-var="firebase_admin_key_file=/path/to/key.json"` when running `terraform apply`. Terraform will:

- create the `functions_bucket` (if provided),
- create a zip archive from the `function_source_dir` (default `../backend` relative to the `terraform/` folder),
- upload the archive to the `functions_bucket`,
- create a Cloud Function resource and make it publicly invokable (the function code itself performs Firebase ID token verification),

Example:

```bash
terraform apply \
	-var="project_id=YOUR_PROJECT" \
	-var="images_bucket=your-unique-bucket-name" \
	-var="functions_bucket=your-unique-functions-bucket" \
	-var="firebase_admin_key_file=/path/to/service-account.json"
```

After apply, `terraform output function_url` will provide the function's HTTPS trigger URL (if created).



```

This is a starting point. You will likely need to extend it to provision Firestore in Native mode and connect Firebase Hosting resources.
